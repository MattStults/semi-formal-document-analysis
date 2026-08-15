"""The construction the preflight's resume_hazard.py omits: the process dies
AFTER the redraw succeeded and the module .json is on disk, but BEFORE (and
during) version.write_stamp.  Also: die after the stamp but before flush()."""
import copy, json, os, shutil, sys, tempfile
P1="/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/walkthrough/paper_pipeline/phase_1"
sys.path.insert(0,P1)
import translate as T, version as V, schema
sys.path.insert(0,os.path.join(P1,"_debug_gen11","preflight_replay"))
import resume_hazard as RH

CLAUSE="m0091"
def main():
    good=json.dumps(RH._good_module()); bad=json.dumps(RH._bad(CLAUSE))
    tmp=tempfile.mkdtemp(prefix="resume_gap_")
    class Killed(BaseException): pass
    try:
        for label, victim in (("D. killed INSIDE version.write_stamp "
                               "(module .json + .lp already on disk)", "write_stamp"),
                              ("E. killed right AFTER the stamp, before run.json flush",
                               "after_stamp")):
            cfg=RH._cfg(tmp,label[:1]); rundir=os.path.join(tmp,label[:1])
            real=V.write_stamp
            def patched(outdir,cid,st,_real=real,_v=victim):
                if _v=="write_stamp": raise Killed("SIGKILL inside write_stamp")
                _real(outdir,cid,st); raise Killed("SIGKILL after write_stamp")
            V.write_stamp=patched
            # translate.py did `import version`, so patch the attribute it reads
            T.version.write_stamp=patched
            try:
                T.run(cfg,RH._args(),client_factory=RH._factory([bad,bad,good]))
                print(f"--- {label}: DID NOT RAISE (unexpected)")
            except BaseException as e:
                print(f"\n--- {label} -> raised {type(e).__name__}")
            finally:
                V.write_stamp=real; T.version.write_stamp=real
            print("   files:",sorted(os.listdir(rundir)) if os.path.isdir(rundir) else "ABSENT")
            st,stale=RH._resume_state(tmp,cfg)
            print(f"   resume state for {CLAUSE}: {st}   would re-translate: {stale}")
            if not stale:
                print("   ⛔ HAZARD: a resume would SKIP a clause whose run died mid-write")
            shutil.rmtree(rundir,ignore_errors=True)
    finally:
        shutil.rmtree(tmp,ignore_errors=True)
main()
