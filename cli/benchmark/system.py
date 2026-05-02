"""System introspection: CPU, RAM, OS, and virtualization detection."""

import os
import platform
import re
import subprocess
from dataclasses import dataclass
from typing import Optional

import psutil
from cpuinfo import get_cpu_info


@dataclass
class SystemInfo:
    os: str
    os_version: str
    arch: str
    cpu_model: str
    cpu_cores: int
    cpu_threads: int
    ram_gb: int
    is_virtualized: bool
    virtualization_platform: Optional[str]


def _get_os_info() -> tuple[str, str]:
    """Get OS name and version."""
    system = platform.system()
    if system == "Linux":
        try:
            with open("/etc/os-release") as f:
                lines = f.readlines()
            info = {}
            for line in lines:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    info[k] = v.strip('"')
            os_name = info.get("PRETTY_NAME", info.get("NAME", "Linux"))
            os_version = info.get("VERSION_ID", "")
        except Exception:
            os_name = "Linux"
            os_version = platform.release()
    elif system == "Darwin":
        os_name = "macOS"
        os_version = platform.mac_ver()[0]
    elif system == "Windows":
        os_name = "Windows"
        os_version = platform.win32_ver()[1]
    else:
        os_name = system
        os_version = platform.release()
    return os_name, os_version


def _detect_virtualization_linux() -> tuple[bool, Optional[str]]:
    """Detect virtualization on Linux via multiple methods."""
    # Method 1: /proc/cpuinfo hypervisor flag
    try:
        with open("/proc/cpuinfo") as f:
            cpuinfo = f.read()
        if "hypervisor" in cpuinfo.lower():
            # Try to identify the hypervisor
            for line in cpuinfo.splitlines():
                if line.startswith("vendor_id") or line.startswith("model name"):
                    vendor = line.split(":", 1)[1].strip().lower()
                    if "kvm" in vendor or "qemu" in vendor:
                        return True, "kvm/qemu"
                    if "vmware" in vendor:
                        return True, "vmware"
                    if "microsoft" in vendor or "hyper-v" in vendor:
                        return True, "hyperv"
                    if "parallels" in vendor:
                        return True, "parallels"
            return True, "unknown"
    except Exception:
        pass

    # Method 2: systemd-detect-virt
    try:
        result = subprocess.run(
            ["systemd-detect-virt"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            virt = result.stdout.strip().lower()
            if virt != "none":
                return True, virt
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Method 3: /sys/hypervisor/type
    try:
        with open("/sys/hypervisor/type") as f:
            hv_type = f.read().strip().lower()
            if hv_type:
                return True, hv_type
    except (FileNotFoundError, PermissionError):
        pass

    # Method 4: DMI via /sys/class/dmi/id/
    dmi_paths = {
        "product_name": "/sys/class/dmi/id/product_name",
        "sys_vendor": "/sys/class/dmi/id/sys_vendor",
        "board_vendor": "/sys/class/dmi/id/board_vendor",
    }
    vm_signatures = {
        "kvm": ["kvm", "qemu"],
        "vmware": ["vmware"],
        "hyperv": ["microsoft", "hyper-v", "hyperv"],
        "virtualbox": ["virtualbox"],
        "parallels": ["parallels"],
        "xen": ["xen"],
    }
    try:
        for key, path in dmi_paths.items():
            with open(path) as f:
                value = f.read().strip().lower()
                for platform_name, signatures in vm_signatures.items():
                    for sig in signatures:
                        if sig in value:
                            return True, platform_name
    except (FileNotFoundError, PermissionError):
        pass

    # Method 5: Check for common VM device files
    vm_devices = [
        "/dev/vboxguest",
        "/dev/vmware",
        "/dev/virtio-ports",
    ]
    for dev in vm_devices:
        if os.path.exists(dev):
            return True, "unknown"

    return False, None


def _detect_virtualization_macos() -> tuple[bool, Optional[str]]:
    """Detect virtualization on macOS."""
    try:
        result = subprocess.run(
            ["sysctl", "-n", "hw.optional.x86_64"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Check sysctl for hypervisor hint
    try:
        result = subprocess.run(
            ["sysctl", "machdep.cpu.features"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and "hypervisor" in result.stdout.lower():
            return True, "unknown"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Check system_profiler for VM signatures
    try:
        result = subprocess.run(
            ["system_profiler", "SPHardwareDataType"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            output = result.stdout.lower()
            if "virtual" in output or "parallels" in output or "vmware" in output:
                # Try to identify which one
                if "parallels" in output:
                    return True, "parallels"
                if "vmware" in output:
                    return True, "vmware"
                if "virtualbox" in output:
                    return True, "virtualbox"
                return True, "unknown"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return False, None


def _detect_virtualization_windows() -> tuple[bool, Optional[str]]:
    """Detect virtualization on Windows."""
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             "Get-WmiObject Win32_ComputerSystem | Select-Object Manufacturer, Model | Format-List"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            output = result.stdout.lower()
            vm_signatures = {
                "hyperv": ["microsoft corporation", "hyper-v"],
                "vmware": ["vmware"],
                "virtualbox": ["virtualbox", "innotek"],
                "parallels": ["parallels"],
                "xen": ["xen"],
            }
            for platform_name, signatures in vm_signatures.items():
                for sig in signatures:
                    if sig in output:
                        return True, platform_name
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Check CPUID hypervisor bit via registry
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             "Get-ItemProperty -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\SystemInformation' -ErrorAction SilentlyContinue | Select-Object HypervisorPresent"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and "true" in result.stdout.lower():
            return True, "unknown"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return False, None


def detect_virtualization() -> tuple[bool, Optional[str]]:
    """Cross-platform virtualization detection."""
    system = platform.system()
    if system == "Linux":
        return _detect_virtualization_linux()
    elif system == "Darwin":
        return _detect_virtualization_macos()
    elif system == "Windows":
        return _detect_virtualization_windows()
    return False, None


def get_system_info() -> SystemInfo:
    """Gather comprehensive system information."""
    os_name, os_version = _get_os_info()
    arch = platform.machine()
    cpu_info = get_cpu_info()
    
    cpu_model = cpu_info.get("brand_raw", cpu_info.get("brand", "Unknown"))
    # Clean up CPU model string
    cpu_model = re.sub(r"\s+", " ", cpu_model).strip()
    
    cpu_cores = psutil.cpu_count(logical=False) or 0
    cpu_threads = psutil.cpu_count(logical=True) or 0
    ram_bytes = psutil.virtual_memory().total
    ram_gb = round(ram_bytes / (1024 ** 3))
    
    is_virt, virt_platform = detect_virtualization()
    
    return SystemInfo(
        os=os_name,
        os_version=os_version,
        arch=arch,
        cpu_model=cpu_model,
        cpu_cores=cpu_cores,
        cpu_threads=cpu_threads,
        ram_gb=ram_gb,
        is_virtualized=is_virt,
        virtualization_platform=virt_platform,
    )
