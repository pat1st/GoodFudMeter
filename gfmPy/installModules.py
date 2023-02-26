def install(package):
    # This function will install a package if it is not present
    from importlib import import_module
    try:
        import_module(package)
    except:
        from sys import executable as se
        from subprocess import check_call
        check_call([se, '-m', 'pip', '-q', 'install', package])


for package in ['google.cloud.language', 'gnews', 'azure-cosmos', 'datetime']:
    install(package)
