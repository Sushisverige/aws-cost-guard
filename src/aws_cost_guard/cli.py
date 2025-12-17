from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

import boto3
import typer
from botocore.config import Config
from botocore.exceptions import ClientError
from rich.console import Console
from rich.table import Table


app = typer.Typer(add_completion=False, help="AWS Cost Guard: read-only cost risk scanner (beginner friendly)")
console = Console()


# ---- helpers ----

def _session(profile: str, region: str):
    # retriesを少し強めに（ネットが不安定でも落ちにくくする）
    cfg = Config(
        region_name=region,
        retries={"max_attempts": 10, "mode": "standard"},
    )
    return boto3.Session(profile_name=profile, region_name=region, botocore_session=None), cfg


def _client(service: str, profile: str, region: str):
    sess, cfg = _session(profile, region)
    return sess.client(service, config=cfg)


def print_table(title: str, columns: Sequence[str], rows: Sequence[Sequence[Any]]) -> None:
    table = Table(title=title, show_header=True, header_style="bold")
    for c in columns:
        table.add_column(str(c))
    for r in rows:
        table.add_row(*[str(x) for x in r])
    console.print(table)


def _regions(profile: str) -> List[str]:
    c = _client("ec2", profile, "us-east-1")  # リージョン一覧はどこでもOK
    resp = c.describe_regions(AllRegions=False)
    return sorted([r["RegionName"] for r in resp.get("Regions", [])])


# ---- commands ----

@app.command()
def whoami(
    profile: str = typer.Option("portfolio", "--profile", help="AWS CLI profile"),
    region: str = typer.Option("ap-northeast-1", "--region", help="AWS region"),
):
    """今の認証先（アカウント/ARN）を表示する"""
    sts = _client("sts", profile, region)
    ident = sts.get_caller_identity()
    console.print(
        {
            "UserId": ident.get("UserId"),
            "Account": ident.get("Account"),
            "Arn": ident.get("Arn"),
        }
    )


@app.command()
def ec2(
    profile: str = "portfolio",
    region: str = "ap-northeast-1",
    all: bool = typer.Option(False, "--all-regions", help="全リージョンをチェック"),
):
    """EC2が動いていないか（pending/running/stopping/stopped）をチェック"""
    regions = _regions(profile) if all else [region]
    rows: List[Tuple[str, str, str]] = []

    for r in regions:
        ec2c = _client("ec2", profile, r)
        resp = ec2c.describe_instances(
            Filters=[{"Name": "instance-state-name", "Values": ["pending", "running", "stopping", "stopped"]}]
        )
        for res in resp.get("Reservations", []):
            for inst in res.get("Instances", []):
                rows.append((r, inst.get("InstanceId", ""), inst.get("State", {}).get("Name", "")))

    if rows:
        print_table("EC2 instances found", ["Region", "InstanceId", "State"], rows)
        console.print("⚠️  EC2 は起動/停止していても請求が発生し得ます（特にEBS）。不要なら削除。")
    else:
        console.print("✅ EC2: none found (pending/running/stopping/stopped)")


@app.command()
def ebs(
    profile: str = "portfolio",
    region: str = "ap-northeast-1",
    all: bool = typer.Option(False, "--all-regions", help="全リージョンをチェック"),
):
    """未使用（available）のEBSボリュームが残っていないかチェック"""
    regions = _regions(profile) if all else [region]
    rows: List[Tuple[str, str, int, str]] = []

    for r in regions:
        ec2c = _client("ec2", profile, r)
        resp = ec2c.describe_volumes(Filters=[{"Name": "status", "Values": ["available"]}])
        for v in resp.get("Volumes", []):
            rows.append((r, v.get("VolumeId", ""), int(v.get("Size", 0)), v.get("State", "")))

    if rows:
        print_table("EBS volumes (available) found", ["Region", "VolumeId", "Size(GB)", "State"], rows)
        console.print("⚠️  available のEBSは『インスタンスに付いてなくても』課金されます。不要なら削除。")
    else:
        console.print("✅ EBS: no available volumes")


@app.command()
def eip(
    profile: str = "portfolio",
    region: str = "ap-northeast-1",
    all: bool = typer.Option(False, "--all-regions", help="全リージョンをチェック"),
):
    """未割り当て（InstanceIdなし）のElastic IPがないかチェック"""
    regions = _regions(profile) if all else [region]
    rows: List[Tuple[str, str, str]] = []

    for r in regions:
        ec2c = _client("ec2", profile, r)
        resp = ec2c.describe_addresses()
        for a in resp.get("Addresses", []):
            # InstanceId / NetworkInterfaceId が無い＝未関連付け
            if not a.get("InstanceId") and not a.get("NetworkInterfaceId"):
                rows.append((r, a.get("PublicIp", ""), a.get("AllocationId", "")))

    if rows:
        print_table("Elastic IPs (unused) found", ["Region", "PublicIp", "AllocationId"], rows)
        console.print("⚠️  未使用のElastic IPは課金対象になり得ます。不要なら解放。")
    else:
        console.print("✅ EIP: none unused")


@app.command()
def nat(
    profile: str = "portfolio",
    region: str = "ap-northeast-1",
    all: bool = typer.Option(False, "--all-regions", help="全リージョンをチェック"),
):
    """NAT Gatewayが残っていないか（高額になりやすいので）チェック"""
    regions = _regions(profile) if all else [region]
    rows: List[Tuple[str, str, str, str, str]] = []

    for r in regions:
        ec2c = _client("ec2", profile, r)
        try:
            resp = ec2c.describe_nat_gateways(
                Filter=[{"Name": "state", "Values": ["available", "pending"]}]
            )
        except ClientError as e:
            # 一部のアカウント/権限でNAT APIが拒否されることがあるので、落とさず続行
            console.print(f"⚠️  NAT check skipped in {r}: {e.response.get('Error', {}).get('Code')}")
            continue

        for ngw in resp.get("NatGateways", []):
            rows.append(
                (
                    r,
                    ngw.get("NatGatewayId", ""),
                    ngw.get("State", ""),
                    ngw.get("VpcId", ""),
                    ngw.get("SubnetId", ""),
                )
            )

    if rows:
        print_table("NAT Gateways found", ["Region", "NatGatewayId", "State", "VpcId", "SubnetId"], rows)
        console.print("🚨 NAT Gatewayは『時間課金 + データ処理課金』で高額化しやすい。不要なら必ず削除。")
    else:
        console.print("✅ NAT: none found (available/pending)")


@app.command()
def summary(
    profile: str = "portfolio",
    region: str = "ap-northeast-1",
    all: bool = typer.Option(False, "--all-regions", help="全リージョンをチェック"),
):
    """危険そうなものをまとめてチェック（初心者はこれだけでOK）"""
    console.print("=== AWS Cost Guard (read-only) ===")
    whoami(profile, region)
    ec2(profile, region, all)
    ebs(profile, region, all)
    eip(profile, region, all)
    nat(profile, region, all)
