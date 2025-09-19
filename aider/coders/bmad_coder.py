import os
import importlib.resources
from aider.coders.base_coder import Coder

class BMADCoder(Coder):
    edit_format = "bmad"

    def __init__(self, main_model, io, **kwargs):
        super().__init__(main_model, io, **kwargs)
        self.io.tool_output("BMAD Coder initialized")

        # Ported from the BMAD installer
        self.install_bmad_core()

    def install_bmad_core(self):
        core_path = os.path.join(self.root, ".bmad-core")
        if os.path.exists(core_path):
            return

        if not self.io.confirm_ask("No .bmad-core directory found. Install it now?"):
            return

        self.io.tool_output("Installing .bmad-core...")
        os.makedirs(core_path, exist_ok=True)

        try:
            resource_path = "aider.resources.bmad_core"
            for item_name in importlib.resources.contents(resource_path):
                item_path = os.path.join(resource_path.replace(".", "/"), item_name)
                if importlib.resources.is_resource(resource_path, item_name):
                    content = importlib.resources.read_text(resource_path, item_name)
                    dest_path = os.path.join(core_path, item_name)
                    with open(dest_path, "w", encoding="utf-8") as f:
                        f.write(content)
                else: # it's a directory
                    self.copy_bmad_assets(item_path, core_path)
        except Exception as e:
            self.io.tool_error(f"Error installing .bmad-core: {e}")
            return

        self.io.tool_output(".bmad-core installation complete.")

    def copy_bmad_assets(self, src, dst):
        if "__pycache__" in src:
            return

        dst_path = os.path.join(dst, os.path.basename(src))
        os.makedirs(dst_path, exist_ok=True)

        src_pkg = src.replace("/",".")

        for item_name in importlib.resources.contents(src_pkg):
            item_path = os.path.join(src, item_name)
            if importlib.resources.is_resource(src_pkg, item_name):
                content = importlib.resources.read_text(src_pkg, item_name)
                dest_path = os.path.join(dst_path, item_name)
                with open(dest_path, "w", encoding="utf-8") as f:
                    f.write(content)
            else: # it's a directory
                self.copy_bmad_assets(item_path, dst_path)
