"""Check required agent skill files before generating; never installs silently."""
import argparse,json,os,re,sys
from pathlib import Path

REQUIRED={
    'remotion-best-practices':'Remotion workflow routing and constraints',
    'remotion-create':'Composition/project creation',
    'remotion-markup':'Frame-driven React/SVG animation',
    'remotion-render':'Render and export guidance',
}
REPO='remotion-dev/skills'

def default_roots():
    home=Path.home();cwd=Path.cwd();roots=[]
    if os.environ.get('CODEX_HOME'):roots.append(Path(os.environ['CODEX_HOME'])/'skills')
    for base in [home,cwd,*list(cwd.parents)[:4]]:
        roots.extend(base/name/'skills' for name in ['.agents','.codex','.claude','.cursor','.opencode'])
    roots.extend(Path(p) for p in os.environ.get('SKILL_ROOTS','').split(os.pathsep) if p)
    return list(dict.fromkeys(roots))

def check(roots):
    found={};invalid=[]
    for root in roots:
        for name in REQUIRED:
            file=root/name/'SKILL.md'
            if not file.is_file():continue
            body=file.read_text(encoding='utf-8-sig',errors='replace')
            front=body.split('---',2)
            valid=len(front)>=3 and bool(re.search(r'^name:\s*[\'\"]?'+re.escape(name)+r'[\'\"]?\s*$',front[1],re.M)) and 'remotion' in body.lower() and len(front[2].strip())>120
            # A directory name alone does not prove the skill has usable content.
            if valid:found.setdefault(name,str(file.resolve()))
            else:invalid.append(str(file))
    missing=[n for n in REQUIRED if n not in found]
    return {'all_pass':not missing,'required':REQUIRED,'found':found,'missing':missing,
            'invalid_skill_files':invalid,'scanned_roots':[str(p) for p in roots],
            'install_command':'npx skills add '+REPO+' --skill '+' '.join(missing or REQUIRED)+' -y',
            'source':'https://github.com/'+REPO,
            'note':'File checks establish availability, not semantic quality. The agent must read relevant skill instructions and verify image/file/command capabilities. Built-in or equivalent skills require agent review.'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--skill-root',type=Path,action='append')
    p.add_argument('--json',action='store_true');p.add_argument('--save',type=Path);a=p.parse_args()
    result=check(a.skill_root if a.skill_root else default_roots())
    if a.save:a.save.parent.mkdir(parents=True,exist_ok=True);a.save.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    if a.json:print(json.dumps(result,ensure_ascii=False,indent=2))
    else:
        print('SKILL CHECK:', 'PASS' if result['all_pass'] else 'MISSING OR INVALID')
        for name in REQUIRED:print(('OK ' if name in result['found'] else 'INSTALL ')+name)
        if not result['all_pass']:print(result['install_command'])
    sys.exit(0 if result['all_pass'] else 2)

if __name__=='__main__':main()
