from pythonforandroid.recipe import CythonRecipe, IncludedFilesBehaviour


class VsextRecipe(IncludedFilesBehaviour, CythonRecipe):
    version = "0.1.0"
    name = "vsext"
    depends = ["setuptools"]
    src_filename = "../../vsext"
    cython_args = ["-3", "--cplus"]
    need_stl_shared = True

    def build_cython_components(self, arch):
        return super().build_cython_components(arch)


recipe = VsextRecipe()

