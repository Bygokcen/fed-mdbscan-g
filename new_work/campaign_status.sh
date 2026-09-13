#!/usr/bin/env bash
set -euo pipefail
C="${1:-$(dirname "$0")/results/validated/audit-v2/full_20260910}"
python3 - "$C" <<'PY'
import json,sys,os,time
from pathlib import Path
root=Path(sys.argv[1]);manifest=json.loads((root/'campaign.json').read_text())
path=root/'parallel_progress.json'
if not path.exists():path=root/'status.json'
s=json.loads(path.read_text());pid=s.get('pid');alive=False
if pid and Path(f'/proc/{pid}/cmdline').exists():
    cmd=Path(f'/proc/{pid}/cmdline').read_bytes().decode(errors='replace')
    alive=root.name in cmd and ('run_campaign_parallel' in cmd or 'run_audit_campaign' in cmd)
written=len(list(root.glob('runs/*/*/scenario_*/runs/*.json')))
recovery_path=root/'recovery_status.json'
if recovery_path.exists():
    recovery=json.loads(recovery_path.read_text());rp=recovery.get('pid')
    try:
        rc=Path(f'/proc/{rp}/cmdline').read_bytes().decode(errors='replace')
        recovery_alive='complete_audit_recovery.py' in rc and root.name in rc
    except OSError: recovery_alive=False
    print(f"Tamamlama süreci: {recovery.get('state')} | PID: {rp} | canlı: {recovery_alive}")
    if recovery_alive:print(f"Tamamlama aşaması/işi: {recovery.get('job','tek işçili tekrarlar')} | kayıt: recovery_status.json")
print(f"Durum: {s.get('state')} | süreç: {pid} | canlı: {alive}")
print(f"Yazılmış birim: {written}/{manifest['expected_units']} (dosya sayısı)")
print(f"Son denetimde geçerli: {s.get('valid_units','henüz yok')} | başarısız: {s.get('failed_units','ayrıntı dosyasına bakınız')}")
print(f"Çalışan iş: {len(s.get('in_flight',[]))} | kuyruk: {s.get('queued','?')}")
print(f"Durum kaydı yaşı: {time.time()-s.get('updated_unix',time.time()):.0f} saniye")
print('Doğrulama: external_validation.json | sayısal tanı: diagnostics/ | rapor: report/')
print('Kesin bitiş tahmini verilmez; yöntem/veri kümesi süreleri farklıdır.')
PY
