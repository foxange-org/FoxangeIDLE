import os
import json
import shutil
from dataclasses import dataclass, field
from typing import Optional

def _built_library_dir():
    import foxange
    return os.path.join(
        os.path.dirname(os.path.abspath(foxange.__file__)),
        "lib", "built_library"
    )


def _repo_json_path():
    return os.path.join(_built_library_dir(), "repository_address.json")

@dataclass
class PackageManifest:
    name: str
    version: str = "0.1.0"
    description: str = ""
    author: str = ""
    main: str = ""
    exports: list = field(default_factory=list)
    dependencies: dict = field(default_factory=dict)

def _load_repo() -> dict:
    path = _repo_json_path()
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    return {}


def _save_repo(repo: dict):
    path = _repo_json_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(repo, f, indent=2, ensure_ascii=False)


def _list_installed() -> list[dict]:
    blib = _built_library_dir()
    result = []
    if os.path.exists(blib):
        for name in os.listdir(blib):
            pkg_dir = os.path.join(blib, name)
            manifest_path = os.path.join(pkg_dir, "package.fx.json")
            if os.path.isfile(manifest_path):
                with open(manifest_path, "r", encoding="utf-8") as f:
                    result.append(json.load(f))
    repo = _load_repo()
    import foxange
    foxange_root = os.path.dirname(os.path.abspath(foxange.__file__))
    project_root = os.path.dirname(foxange_root)
    for name, path in repo.items():
        if any(p["name"] == name for p in result):
            continue
        abs_path = os.path.normpath(os.path.join(project_root, path))
        if os.path.isfile(abs_path) and abs_path.endswith(".fx"):
            result.append({
                "name": name,
                "version": "(内置)",
                "description": os.path.basename(abs_path),
                "kind": "builtin",
            })

    return result

def _install_from_dir(source_dir: str, manifest: dict):
    name = manifest["name"]
    version = manifest.get("version", "0.1.0")

    blib = _built_library_dir()
    os.makedirs(blib, exist_ok=True)
    install_dir = os.path.join(blib, name)
    if os.path.exists(install_dir):
        shutil.rmtree(install_dir)

    shutil.copytree(source_dir, install_dir)

    repo = _load_repo()

    main_file = manifest.get("main", "")
    if main_file:
        main_path = os.path.join(install_dir, main_file)
        repo[name] = main_path

    for export_name in manifest.get("exports", []):
        repo[export_name] = os.path.join(install_dir, export_name + ".fx")

    _save_repo(repo)

    deps = manifest.get("dependencies", {})
    missing = []
    for dep_name, dep_ver in deps.items():
        if not _is_installed(dep_name):
            missing.append(f"{dep_name} (>={dep_ver})")

    if missing:
        print(f"  缺少依赖: {', '.join(missing)}（请手动安装）")

    return name, version


def install(source: str):
    import tempfile
    if source.lower().endswith(".zip"):
        if not os.path.isfile(source):
            raise FileNotFoundError(f"找不到压缩包: {source}")

        tmpdir = tempfile.mkdtemp(prefix="foxpkg_")
        try:
            shutil.unpack_archive(source, tmpdir, "zip")

            candidates = []
            for root, dirs, files in os.walk(tmpdir):
                depth = root[len(tmpdir):].count(os.sep)
                if depth > 1:
                    continue
                if "package.fx.json" in files:
                    candidates.append(root)

            if not candidates:
                raise FileNotFoundError(f"压缩包中未找到 package.fx.json")

            source_dir = tmpdir if tmpdir in candidates else candidates[0]
            manifest_path = os.path.join(source_dir, "package.fx.json")
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)

            name, version = _install_from_dir(source_dir, manifest)
            print(f"已安装 {name} {version} (from zip)")
            return name, version
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    source_dir = source
    manifest_path = os.path.join(source_dir, "package.fx.json")
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"找不到 {manifest_path}，该目录不是一个合法的 Foxange 包")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    name, version = _install_from_dir(source_dir, manifest)
    print(f"已安装 {name} {version}")
    return name, version


def uninstall(pkg_name: str):
    blib = _built_library_dir()
    install_dir = os.path.join(blib, pkg_name)
    install_dir_abs = os.path.abspath(install_dir)

    if not os.path.exists(install_dir):
        raise FileNotFoundError(f"包 '{pkg_name}' 未安装")

    shutil.rmtree(install_dir)

    repo = _load_repo()
    keys_to_remove = [
        k for k, v in repo.items()
        if os.path.abspath(v).startswith(install_dir_abs + os.sep)
        or os.path.abspath(v) == install_dir_abs
    ]
    for k in keys_to_remove:
        del repo[k]
    _save_repo(repo)

    print(f"已卸载 {pkg_name}")


def _is_installed(pkg_name: str) -> bool:
    manifest_path = os.path.join(_built_library_dir(), pkg_name, "package.fx.json")
    return os.path.exists(manifest_path)

def list_packages():
    packages = _list_installed()
    if not packages:
        print("（无已安装的包）")
        return

    print(f"{'名称':<20} {'版本':<10} {'类型':<6} {'描述'}")
    print("-" * 60)
    for pkg in packages:
        desc = pkg.get("description", "")[:30]
        ver = pkg.get("version", "?")
        kind = "内置" if pkg.get("kind") == "builtin" else "包"
        print(f"{pkg['name']:<20} {ver:<10} {kind:<6} {desc}")


def info(pkg_name: str):
    manifest_path = os.path.join(_built_library_dir(), pkg_name, "package.fx.json")
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"包 '{pkg_name}' 未安装")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    print(f"名称:     {manifest['name']}")
    print(f"版本:     {manifest.get('version', '-')}")
    print(f"作者:     {manifest.get('author', '-')}")
    print(f"描述:     {manifest.get('description', '-')}")
    print(f"入口:     {manifest.get('main', '-')}")
    print(f"导出:     {', '.join(manifest.get('exports', [])) or '-'}")
    deps = manifest.get("dependencies", {})
    if deps:
        print(f"依赖:")
        for dep, ver in deps.items():
            print(f"  - {dep} >={ver}")
    else:
        print(f"依赖:     无")

def init_package(target_dir: str, name: str):
    os.makedirs(target_dir, exist_ok=True)

    manifest = {
        "name": name,
        "version": "0.1.0",
        "description": "",
        "author": "",
        "main": "main.fx",
        "exports": [],
        "dependencies": {},
    }

    manifest_path = os.path.join(target_dir, "package.fx.json")
    if os.path.exists(manifest_path):
        print(f"警告: {manifest_path} 已存在，将覆盖")

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    main_path = os.path.join(target_dir, "main.fx")
    if not os.path.exists(main_path):
        with open(main_path, "w", encoding="utf-8") as f:
            f.write(f'""" {name} 包入口 """\n')
            f.write(f'\n')
            f.write(f'def hello() :\n')
            f.write(f'    print("Hello from {name}!")\n')

    print(f"已初始化包 {name} 在 {target_dir}")
    print(f"  - {manifest_path}")
    print(f"  - {main_path}")
