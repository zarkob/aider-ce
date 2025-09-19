import os
import unittest
from unittest.mock import MagicMock, patch, mock_open

from aider.coders.bmad_coder import BMADCoder

class TestBMADCoder(unittest.TestCase):
    def setUp(self):
        self.mock_io = MagicMock()
        with patch("aider.coders.bmad_coder.BMADCoder.install_bmad_core"):
            self.coder = BMADCoder(main_model=MagicMock(), io=self.mock_io)
        self.coder.root = "/test/repo"
        self.coder.bmad_core_path = os.path.join(self.coder.root, ".bmad-core")

    def test_handle_agent_command_list_agents(self):
        self.mock_io.reset_mock()
        with patch("os.listdir") as mock_listdir, \
             patch("os.path.exists") as mock_exists:
            mock_listdir.return_value = ["analyst.md", "pm.md", "tech_lead.md", "other.txt"]
            mock_exists.return_value = True
            self.coder.handle_agent_command("")
            self.mock_io.tool_output.assert_any_call("Available agents:")
            self.mock_io.tool_output.assert_any_call("  analyst")
            self.mock_io.tool_output.assert_any_call("  pm")
            self.mock_io.tool_output.assert_any_call("  tech_lead")
            # Make sure it doesn't list non-md files
            self.assertEqual(self.mock_io.tool_output.call_count, 4)

    def test_handle_agent_command_switch_agent_success(self):
        agent_name = "analyst"
        persona_content = "You are an analyst."

        with patch("builtins.open", mock_open(read_data=persona_content)) as mock_file, \
             patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True

            self.coder.handle_agent_command(agent_name)

            self.assertEqual(self.coder.active_agent_name, agent_name)
            self.assertEqual(self.coder.active_agent_persona, persona_content)
            self.mock_io.tool_output.assert_called_with(f"Switched to agent: {agent_name}")

    def test_handle_agent_command_switch_agent_not_found(self):
        agent_name = "nonexistent_agent"
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = False
            self.coder.handle_agent_command(agent_name)
            self.mock_io.tool_error.assert_called_with(f"Agent '{agent_name}' not found.")

    def test_execute_create_doc_success(self):
        self.coder.active_agent_name = "pm"
        self.coder.active_agent_persona = "You are a product manager."
        doc_type = "prd"
        task_instructions = "Create a PRD."
        template_content = "Template for PRD."
        generated_doc = "This is the generated PRD."

        mock_fs = {
            os.path.join(self.coder.bmad_core_path, "tasks", "create-doc.md"): task_instructions,
            os.path.join(self.coder.bmad_core_path, "templates", f"{doc_type}-tmpl.yaml"): template_content,
        }

        with patch("builtins.open", new_callable=mock_open) as m, \
             patch("os.path.exists", side_effect=lambda p: p in mock_fs), \
             patch.object(self.coder, "run") as mock_run, \
             patch("os.makedirs"):

            handles = {}
            def side_effect(p, *args, **kwargs):
                handle = mock_open(read_data=mock_fs.get(p, "")).return_value
                handles[p] = handle
                return handle

            m.side_effect = side_effect
            mock_run.return_value = generated_doc

            self.coder._execute_create_doc([doc_type])

            expected_prompt = (
                f"{self.coder.active_agent_persona}\\n\\n"
                f"{task_instructions}\\n\\n"
                f"Here is the template for the document:\\n\\n"
                f"{template_content}"
            )
            mock_run.assert_called_once_with(with_message=expected_prompt, preproc=False)

            output_path = os.path.join(self.coder.root, "docs", f"{doc_type}.md")
            self.assertIn(output_path, handles)
            handles[output_path].write.assert_called_once_with(generated_doc)
            self.mock_io.tool_output.assert_called_with(f"Created document {output_path} and added it to the chat.")

    def test_execute_advanced_elicitation_success(self):
        self.coder.active_agent_name = "analyst"
        self.coder.active_agent_persona = "You are an analyst."
        doc_path = "docs/prd.md"
        doc_content = "Initial PRD."
        task_instructions = "Refine this document."

        mock_fs = {
            doc_path: doc_content,
            os.path.join(self.coder.bmad_core_path, "tasks", "advanced-elicitation.md"): task_instructions,
        }

        with patch("builtins.open", new_callable=mock_open) as m, \
             patch("os.path.exists", side_effect=lambda p: p in mock_fs), \
             patch.object(self.coder, "run") as mock_run:

            m.side_effect = lambda p, *args, **kwargs: mock_open(read_data=mock_fs.get(p, "")).return_value

            self.coder._execute_advanced_elicitation([doc_path])

            expected_prompt = (
                f"{self.coder.active_agent_persona}\\n\\n"
                f"{task_instructions}\\n\\n"
                f"Here is the document to be refined:\\n\\n"
                f"{doc_content}"
            )
            mock_run.assert_called_once_with(with_message=expected_prompt, preproc=False)
            self.mock_io.tool_output.assert_called_with(f"Starting advanced elicitation for {doc_path} with agent {self.coder.active_agent_name}...")


if __name__ == "__main__":
    unittest.main()
