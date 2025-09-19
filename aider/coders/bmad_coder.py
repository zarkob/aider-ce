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
        self.active_workflow = None
        self.active_phase = None
        self.active_task = None
        self.current_phase_index = 0
        self.current_task_index = -1

        # BMAD core is installed by running `/bmad init`

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

    def handle_agent_command(self, args_str):
        args = args_str.split()
        if len(args) == 0:
            agents = self.get_available_agents()
            if agents:
                self.io.tool_output("Available agents:")
                for agent in agents:
                    self.io.tool_output(f"  {agent}")
            else:
                self.io.tool_output("No agents found.")
            return

        agent_name = args[0]
        persona = self.load_agent(agent_name)

        if persona:
            self.active_agent_name = agent_name
            self.active_agent_persona = persona
            self.io.tool_output(f"Switched to agent: {agent_name}")
        else:
            self.io.tool_error(f"Agent '{agent_name}' not found.")

    def handle_task_command(self, args_str):
        args = args_str.split()
        if len(args) < 1:
            self.io.tool_error("Usage: /bmad task <task_name> [task_args...]")
            return

        task_name = args[0]
        task_args = args[1:]

        task_map = {
            "create-doc": self._execute_create_doc,
            "advanced-elicitation": self._execute_advanced_elicitation,
            "shard-doc": self._execute_shard_doc,
            "create-next-story": self._execute_create_next_story,
            "develop-story": self._execute_develop_story,
            "review-story": self._execute_review_story,
        }

        if task_name in task_map:
            task_map[task_name](task_args)
        else:
            self.io.tool_error(f"Unknown task: {task_name}")

    def show_bmad_status(self):
        if not self.active_workflow:
            self.io.tool_output("No active BMAD workflow.")
            if self.active_agent_name:
                self.io.tool_output(f"Current agent: {self.active_agent_name}")
            return

        self.io.tool_output("BMAD Status:")
        self.io.tool_output(
            "  Workflow:"
            f" {self.active_workflow.get('workflow', {}).get('name', 'Unnamed Workflow')}"
        )
        self.io.tool_output(f"  Phase: {self.active_phase or 'N/A'}")
        self.io.tool_output(f"  Task: {self.active_task or 'N/A'}")
        self.io.tool_output(f"  Agent: {self.active_agent_name or 'N/A'}")

        # Suggest the next step if a workflow is active
        if self.active_task:
            self.io.tool_output(
                f"\nNext step: Run task '{self.active_task}' with agent"
                f" '{self.active_agent_name}'."
            )
            self.io.placeholder = f"/bmad task {self.active_task} "

    def handle_workflow_command(self, args_str):
        try:
            import yaml
        except ImportError:
            self.io.tool_error("Please install pyyaml `pip install pyyaml` to use workflows.")
            return

        workflow_dir = os.path.join(self.bmad_core_path, "workflows")
        if not os.path.exists(workflow_dir):
            self.io.tool_error("Workflows directory not found.")
            return

        args = args_str.split()
        if len(args) == 0:
            self.io.tool_output("Available workflows:")
            for fname in os.listdir(workflow_dir):
                if fname.endswith(".yml") or fname.endswith(".yaml"):
                    self.io.tool_output(f"  - {fname.split('.')[0]}")
            return

        workflow_name = args[0]
        workflow_file = os.path.join(workflow_dir, f"{workflow_name}.yml")
        if not os.path.exists(workflow_file):
            workflow_file = os.path.join(workflow_dir, f"{workflow_name}.yaml")
            if not os.path.exists(workflow_file):
                self.io.tool_error(f"Workflow '{workflow_name}' not found.")
                return

        with open(workflow_file, "r") as f:
            try:
                workflow_data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                self.io.tool_error(f"Error parsing workflow file: {e}")
                return

        self.active_workflow = workflow_data
        self.current_phase_index = 0
        self.current_task_index = -1
        self.io.tool_output(
            f"Started workflow: {workflow_data.get('workflow', {}).get('name', workflow_name)}"
        )
        self.set_next_workflow_step()

    def set_next_workflow_step(self):
        if not self.active_workflow:
            return

        self.current_task_index += 1

        sequence = self.active_workflow.get("workflow", {}).get("sequence", [])

        if self.current_task_index >= len(sequence):
            self.io.tool_output("Workflow completed.")
            self.active_workflow = None
            self.active_phase = None
            self.active_task = None
            self.active_agent_name = None
            self.current_phase_index = 0
            self.current_task_index = -1
            self.io.placeholder = ""
            return

        next_step = sequence[self.current_task_index]
        self.active_agent_name = next_step.get("agent")
        self.load_agent(self.active_agent_name)

        if "creates" in next_step:
            self.active_task = f"create {next_step['creates']}"
        elif "updates" in next_step:
            self.active_task = f"update {next_step['updates']}"
        elif "action" in next_step:
            self.active_task = next_step["action"]
        else:
            self.active_task = "unnamed task"

        self.active_phase = next_step.get("phase")

        self.io.tool_output(
            f"Next step: Run task '{self.active_task}' with agent"
            f" '{self.active_agent_name}'."
        )
        self.io.placeholder = f"@{self.active_agent_name} {self.active_task}"

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
        self.set_next_workflow_step()

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
        self.set_next_workflow_step()


    def install_bmad_core(self):
        prompt = "Install the .bmad-core directory with templates and tasks?"
        if os.path.exists(self.bmad_core_path):
            prompt = ".bmad-core is already installed. Reinstall and overwrite?"

        if not self.io.confirm_ask(prompt):
            return

        if os.path.exists(self.bmad_core_path):
            import shutil
            shutil.rmtree(self.bmad_core_path)

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

    def _execute_shard_doc(self, args):
        if len(args) == 0:
            self.io.tool_error("Usage: /task shard-doc <document_path>")
            return

        doc_path = args[0]

        if not os.path.exists(doc_path):
            self.io.tool_error(f"Document not found: {doc_path}")
            return

        script_path = os.path.join(self.bmad_core_path, "tasks", "shard-doc.py")
        result = self.run_cmd(f"python3 {script_path} {doc_path}")
        self.io.tool_output(result)
        self.set_next_workflow_step()

    def _execute_create_next_story(self, args):
        script_path = os.path.join(self.bmad_core_path, "tasks", "create-next-story.py")
        prompt = self.run_cmd(f"python3 {script_path}")

        if not self.active_agent_name:
            self.io.tool_error("No active agent. Please select one with /agent <agent_name>.")
            return

        if not self.active_agent_persona:
            self.load_agent(self.active_agent_name)

        full_prompt = f"{self.active_agent_persona}\n\n{prompt}"

        self.io.tool_output("Generating next story...")
        story_content = self.run(with_message=full_prompt, preproc=False)

        if not story_content:
            self.io.tool_error("Failed to generate story.")
            return

        stories_dir = "docs/stories"
        os.makedirs(stories_dir, exist_ok=True)

        story_num = 1
        while os.path.exists(os.path.join(stories_dir, f"story-{story_num}.md")):
            story_num += 1

        story_filename = f"story-{story_num}.md"

        with open(os.path.join(stories_dir, story_filename), 'w') as story_file:
            story_file.write(story_content)

        self.io.tool_output(f"Created story: {os.path.join(stories_dir, story_filename)}")
        self.set_next_workflow_step()

    def _execute_develop_story(self, args):
        if len(args) == 0:
            self.io.tool_error("Usage: /task develop-story <story_path>")
            return

        story_path = args[0]

        if not os.path.exists(story_path):
            self.io.tool_error(f"Story not found: {story_path}")
            return

        script_path = os.path.join(self.bmad_core_path, "tasks", "develop-story.py")
        prompt = self.run_cmd(f"python3 {script_path} {story_path}")

        if not self.active_agent_name:
            self.io.tool_error("No active agent. Please select one with /agent <agent_name>.")
            return

        if not self.active_agent_persona:
            self.load_agent(self.active_agent_name)

        full_prompt = f"{self.active_agent_persona}\n\n{prompt}"

        self.io.tool_output("Generating code changes...")
        code_changes = self.run(with_message=full_prompt, preproc=False)

        if not code_changes:
            self.io.tool_error("Failed to generate code changes.")
            return

        self.io.tool_output(code_changes)
        self.set_next_workflow_step()

    def _execute_review_story(self, args):
        if len(args) < 2:
            self.io.tool_error("Usage: /task review-story <story_path> \"<code_changes>\"")
            return

        story_path = args[0]
        code_changes = args[1]

        if not os.path.exists(story_path):
            self.io.tool_error(f"Story not found: {story_path}")
            return

        script_path = os.path.join(self.bmad_core_path, "tasks", "review-story.py")
        prompt = self.run_cmd(f"python3 {script_path} {story_path} \"{code_changes}\"")

        if not self.active_agent_name:
            self.io.tool_error("No active agent. Please select one with /agent <agent_name>.")
            return

        if not self.active_agent_persona:
            self.load_agent(self.active_agent_name)

        full_prompt = f"{self.active_agent_persona}\n\n{prompt}"

        self.io.tool_output("Reviewing code changes...")
        feedback = self.run(with_message=full_prompt, preproc=False)

        if not feedback:
            self.io.tool_error("Failed to generate feedback.")
            return

        self.io.tool_output(feedback)
        self.set_next_workflow_step()
