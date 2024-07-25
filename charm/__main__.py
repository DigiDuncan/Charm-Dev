# nuitka-project: --include-package-data=charm
# nuitka-project: --windows-icon-from-ico=charm\data\images\charm-icon32t.png
# nuitka-project: --force-stderr-spec=err.txt
# nuitka-project: --windows-console-mode=disable
# nuitka-project: --product-name=Charm
# nuitka-project: --product-version=0.0.0.1
from charm import main

if __name__ == "__main__":
    main.main()
