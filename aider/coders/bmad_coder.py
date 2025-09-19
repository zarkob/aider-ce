import os
import importlib.resources
from aider.coders.base_coder import Coder

class BMADCoder(Coder):
    edit_format = "bmad"

    def __init__(self, main_model, io, **kwargs):
        super().__init__(main_model, io, **kwargs)
        self.io.tool_output("BMAD Coder initialized")

        self.bmad_core_path = os.path.join(self.root, ".bmad-core")
        self.agents = {}
        self.active_agent_name = None
        self.active_agent_persona = None

        # Ported from the BMAD installer
        self.install_bmad_core()

    def get_available_agents(self):
        agents_path = os.path.join(self.bmad_core_path, "agents")
        if not os.path.exists(agents_path):
            return []

        agents = []
        for a in os.listdir(agents_path):
            if a.endswith(".md"):
                agents.append(a.replace(".md", ""))
        return agents

    def load_agent(self, agent_name):
        if agent_name in self.agents:
            return self.agents[agent_name]

        agent_path = os.path.join(self.bmad_core_path, "agents", agent_name + ".md")
        if not os.path.exists(agent_path):
            return None

        with open(agent_path, "r") as f:
            persona = f.read()
            self.agents[agent_name] = persona
            return persona

    def preproc_user_input(self, inp):
        if inp.startswith("/agent"):
            self._handle_agent_command(inp)
            return None
        elif inp.startswith("/task"):
            self._handle_task_command(inp)
            return None
        return super().preproc_user_input(inp)

    def _handle_agent_command(self, inp):
        args = inp.split()
        if len(args) == 1:
            agents = self.get_available_agents()
            if agents:
                self.io.tool_output("Available agents:")
                for agent in agents:
                    self.io.tool_output(f"  {agent}")
            else:
                self.io.tool_output("No agents found.")
            return

        agent_name = args[1]
        persona = self.load_agent(agent_name)

        if persona:
            self.active_agent_name = agent_name
            self.active_agent_persona = persona
            self.io.tool_output(f"Switched to agent: {agent_name}")
        else:
            self.io.tool_error(f"Agent '{agent_name}' not found.")

    def _handle_task_command(self, inp):
        args = inp.split()
        if len(args) < 2:
            self.io.tool_error("Usage: /task <task_name> [task_args...]")
            return

        task_name = args[1]

        if task_name == "create-doc":
            self._execute_create_doc(args[2:])
        elif task_name == "advanced-elicitation":
            self._execute_advanced_elicitation(args[2:])
        else:
            self.io.tool_error(f"Unknown task: {task_name}")

    def _execute_advanced_elicitation(self, args):
        if not self.active_agent_name:
            self.io.tool_error("No active agent. Please select one with /agent <agent_name>.")
            return

        if len(args) == 0:
            self.io.tool_error("Usage: /task advanced-elicitation <document_path>")
            return

        doc_path = args[0]

        if not os.path.exists(doc_path):
            self.io.tool_error(f"Document not found: {doc_path}")
            return

        task_instructions_path = os.path.join(self.bmad_core_path, "tasks", "advanced-elicitation.md")

        if not os.path.exists(task_instructions_path):
            self.io.tool_error(f"Task instructions not found: {task_instructions_path}")
            return

        with open(doc_path, "r") as f:
            doc_content = f.read()

        with open(task_instructions_path, "r") as f:
            task_instructions = f.read()

        prompt = (
            f"{self.active_agent_persona}\\n\\n"
            f"{task_instructions}\\n\\n"
            f"Here is the document to be refined:\\n\\n"
            f"{doc_content}"
        )

        self.io.tool_output(f"Starting advanced elicitation for {doc_path} with agent {self.active_agent_name}...")
        self.run(with_message=prompt, preproc=False)

    def _execute_create_doc(self, args):
        if not self.active_agent_name:
            self.io.tool_error("No active agent. Please select one with /agent <agent_name>.")
            return

        if len(args) == 0:
            self.io.tool_error("Usage: /task create-doc <doc_type>")
            return

        doc_type = args[0]

        task_instructions_path = os.path.join(self.bmad_core_path, "tasks", "create-doc.md")
        template_path = os.path.join(self.bmad_core_path, "templates", f"{doc_type}-tmpl.yaml")

        if not os.path.exists(task_instructions_path):
            self.io.tool_error(f"Task instructions not found: {task_instructions_path}")
            return

        if not os.path.exists(template_path):
            self.io.tool_error(f"Document template not found: {template_path}")
            return

        with open(task_instructions_path, "r") as f:
            task_instructions = f.read()

        with open(template_path, "r") as f:
            template_content = f.read()

        prompt = (
            f"{self.active_agent_persona}\\n\\n"
            f"{task_instructions}\\n\\n"
            f"Here is the template for the document:\\n\\n"
            f"{template_content}"
        )

        self.io.tool_output(f"Generating {doc_type} document with agent {self.active_agent_name}...")

        # Use run() to send the prompt to the LLM and get the response
        generated_content = self.run(with_message=prompt, preproc=False)

        if not generated_content:
            self.io.tool_error("Failed to generate document.")
            return

        output_dir = os.path.join(self.root, "docs")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{doc_type}.md")

        with open(output_path, "w") as f:
            f.write(generated_content)

        self.add_rel_fname(os.path.relpath(output_path, self.root))
        self.io.tool_output(f"Created document {output_path} and added it to the chat.")


    def install_bmad_core(self):
        if os.path.exists(self.bmad_core_path):
            return

        if not self.io.confirm_ask("No .bmad-core directory found. Install it now?"):
            return

        self.io.tool_output("Installing .bmad-core...")
        os.makedirs(self.bmad_core_path, exist_ok=True)

        try:
            resource_path = "aider.resources.bmad_core"
            for item_name in importlib.resources.contents(resource_path):
                item_path = os.path.join(resource_path.replace(".", "/"), item_name)
                if importlib.resources.is_resource(resource_path, item_name):
                    content = importlib.resources.read_text(resource_path, item_name)
                    dest_path = os.path.join(self.bmad_core_path, item_name)
                    with open(dest_path, "w", encoding="utf-8") as f:
                        f.write(content)
                else: # it's a directory
                    self.copy_bmad_assets(item_path, self.bmad_core_path)
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
