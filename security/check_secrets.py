"""Local staged-file check. Reports metadata only; requires preinstalled Gitleaks."""
import json,os,pathlib,re,shutil,subprocess,tempfile

def main():
    os.umask(0o077)
    def git(*args):return subprocess.run(['git',*args],capture_output=True)
    if git('rev-parse','--show-toplevel').returncode:
        print(json.dumps({'ok':False,'reason':'Run from an actual repository checkout'}));return 2
    blocked=[]
    for raw in git('ls-files','-z').stdout.split(b'\0'):
        path=raw.decode('utf-8','replace')
        if not path:continue
        name=pathlib.PurePosixPath(path).name
        if (name=='.env' or name.startswith('.env.')) and name not in ['.env.example','.env.sample']:
            blocked.append({'type':'tracked-runtime-environment','path':path})
        if re.search(r'(?i)(?:private.*key|key.*private).*\.pem$',name):
            blocked.append({'type':'tracked-private-key-path','path':path})
    staged=git('diff','--cached','--name-only','--diff-filter=ACMR','-z').stdout.split(b'\0')
    password_send=re.compile(rb'(?i)(?:password|passphrase)[^\n]*?\bsend(?:\s+--)?\s+"([^"\r\n]+)"')
    for raw in staged:
        path=raw.decode('utf-8','replace')
        if not path.endswith('.exp'):continue
        data=git('show',':'+path).stdout
        if any(b'$' not in m[1] and not m[1].startswith(b'[') for m in password_send.finditer(data)):
            blocked.append({'type':'literal-password-response','path':path})
    if not shutil.which('gitleaks'):
        print(json.dumps({'ok':False,'reason':'Preinstalled Gitleaks required; no automatic install','metadata_findings':blocked}));return 2
    with tempfile.TemporaryDirectory(prefix='redacted-secret-check-') as scratch:
        p=pathlib.Path(scratch);p.chmod(0o700)
        (p/'config.toml').write_text('[extend]\nuseDefault = true\n')
        (p/'ignore').write_text('')
        (p/'report.tmpl').write_text('{{range .}}{{printf "%q" .RuleID}}\t{{printf "%q" .File}}\t{{.StartLine}}\n{{end}}')
        result=subprocess.run(['gitleaks','git','--staged','--redact=100','--ignore-gitleaks-allow','--config',str(p/'config.toml'),'--gitleaks-ignore-path',str(p/'ignore'),'--report-format','template','--report-template',str(p/'report.tmpl'),'--report-path',str(p/'report.tsv'),'--no-banner','--no-color','--log-level','error'],capture_output=True)
        report=p/'report.tsv'
        if result.returncode not in [0,1] or not report.exists():
            print(json.dumps({'ok':False,'reason':'Scanner error; raw output suppressed','metadata_findings':blocked}));return 2
        for line in report.read_text().splitlines():
            rule,path,number=line.split('\t');blocked.append({'type':json.loads(rule),'path':json.loads(path),'line':int(number)})
    print(json.dumps({'ok':not blocked,'metadata_findings':blocked}))
    return 1 if blocked else 0

if __name__=='__main__':raise SystemExit(main())
