class DependencyChecker:
    def check(self, modules: list):
        print("Checking module dependencies...")
        all_names = [m.name for m in modules]

        for module in modules:
            if not hasattr(module, "dependencies"):
                continue
            for dep in module.dependencies:
                if dep not in all_names:
                    print(f"WARNING: Module '{module.name}' requires '{dep}' but it is disabled or missing.")
                else:
                    print(f"OK: '{module.name}' dependency '{dep}' found.")

        print("Dependency check complete.")
