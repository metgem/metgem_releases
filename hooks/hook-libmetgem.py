from PyInstaller.utils.hooks import collect_submodules, collect_data_files, collect_dynamic_libs

hiddenimports = collect_submodules('libmetgem', filter=lambda x: "tests" not in x)

