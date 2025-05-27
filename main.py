import json
from abc import ABC, abstractmethod
import streamlit as st
import os  # Import os for file path handling


# --- Core Skill Classes ---

class Skill(ABC):
    """
    Abstract base class for all skills.
    Defines common attributes and an abstract method for visual representation.
    """

    def __init__(self, name: str, level: int = 0, description: str = ""):
        if not (0 <= level <= 100):
            raise ValueError("Skill level must be between 0 and 100.")
        self.name = name
        self.level = level
        self.description = description

    def update_level(self, new_level: int):
        """Updates the skill level, ensuring it's within bounds."""
        if not (0 <= new_level <= 100):
            raise ValueError("New skill level must be between 0 and 100.")
        self.level = new_level
        st.info(f"Updated '{self.name}' level to {self.level}")

    @abstractmethod
    def get_visual_metaphor(self) -> str:
        """
        Abstract method to return a string representation of the visual metaphor.
        This would be rendered graphically in a real GUI.
        """
        pass

    def to_dict(self) -> dict:
        """Converts the skill object to a dictionary for serialization."""
        return {
            "name": self.name,
            "level": self.level,
            "description": self.description,
            "type": self.__class__.__name__  # Store the class name to reconstruct later
        }


class SoftSkill(Skill):
    """
    Represents a soft skill with a 'mana bar' metaphor.
    Mana bar value is directly proportional to the skill level.
    """

    def __init__(self, name: str, level: int = 0, description: str = ""):
        super().__init__(name, level, description)
        self._mana_bar_value = self._calculate_mana_bar()

    def _calculate_mana_bar(self) -> int:
        """Calculates the mana bar value (0-100) based on level."""
        return self.level

    def update_level(self, new_level: int):
        """Updates level and recalculates mana bar."""
        super().update_level(new_level)
        self._mana_bar_value = self._calculate_mana_bar()

    def get_visual_metaphor(self) -> str:
        """Returns a string representation of the mana bar."""
        filled_blocks = int(self._mana_bar_value / 10)  # 10 blocks for 100%
        empty_blocks = 10 - filled_blocks
        return f"Mana: [{'█' * filled_blocks}{'░' * empty_blocks}] ({self._mana_bar_value}%)"


class HardSkill(Skill):
    """
    Represents a hard skill with an 'XP tree' metaphor.
    XP tree progress is represented by 'stages' based on level.
    """
    XP_STAGES = {
        0: "Seed",
        10: "Sapling",
        30: "Young Tree",
        60: "Mature Tree",
        90: "Ancient Tree"
    }

    def __init__(self, name: str, level: int = 0, description: str = ""):
        super().__init__(name, level, description)
        self._xp_tree_stage = self._calculate_xp_tree_stage()

    def _calculate_xp_tree_stage(self) -> str:
        """Determines the XP tree stage based on level."""
        current_stage = "Unknown"
        sorted_stages = sorted(self.XP_STAGES.items())
        for threshold, stage_name in sorted_stages:
            if self.level >= threshold:
                current_stage = stage_name
            else:
                break  # Levels are sorted, so we can stop
        return current_stage

    def update_level(self, new_level: int):
        """Updates level and recalculates XP tree stage."""
        super().update_level(new_level)
        self._xp_tree_stage = self._calculate_xp_tree_stage()

    def get_visual_metaphor(self) -> str:
        """Returns a string representation of the XP tree stage."""
        return f"XP Tree: {self._xp_tree_stage} (Level: {self.level})"


# --- Skill Category Management ---

class SkillCategory:
    """
    Manages a collection of skills within a specific category.
    Supports adding, removing, and updating skills.
    """

    def __init__(self, name: str):
        self.name = name
        self.skills: dict[str, Skill] = {}  # Store skills by name for easy lookup

    def add_skill(self, skill: Skill):
        """Adds a skill to the category."""
        if skill.name in self.skills:
            st.warning(f"Warning: Skill '{skill.name}' already exists in category '{self.name}'.")
        self.skills[skill.name] = skill
        st.success(f"Added skill '{skill.name}' to category '{self.name}'.")

    def get_skill(self, skill_name: str) -> Skill | None:
        """Retrieves a skill by name."""
        return self.skills.get(skill_name)

    def remove_skill(self, skill_name: str):
        """Removes a skill from the category."""
        if skill_name in self.skills:
            del self.skills[skill_name]
            st.success(f"Removed skill '{skill_name}' from category '{self.name}'.")
        else:
            st.error(f"Error: Skill '{skill_name}' not found in category '{self.name}'.")

    def display_category_skills(self):
        """Displays all skills within this category."""
        st.subheader(f"Category: {self.name}")
        if not self.skills:
            st.write("No skills in this category yet.")
            return
        for skill_name, skill in self.skills.items():
            st.markdown(f"**{skill.name}** (Level: {skill.level})")
            st.write(f"Description: {skill.description}")
            st.write(skill.get_visual_metaphor())
            if isinstance(skill, SoftSkill):
                st.progress(skill.level / 100.0, text=f"Mana: {skill.level}%")
            elif isinstance(skill, HardSkill):
                # For XP tree, a simple progress bar can represent the level
                st.progress(skill.level / 100.0, text=f"XP Progress: {skill.level}% ({skill._xp_tree_stage})")

    def to_dict(self) -> dict:
        """Converts the category and its skills to a dictionary for serialization."""
        return {
            "name": self.name,
            "skills": [skill.to_dict() for skill in self.skills.values()]
        }


# --- Platform Manager ---

class SkillPlatformManager:
    """
    Manages all skill categories and provides overall platform functionalities.
    """

    def __init__(self):
        self.categories: dict[str, SkillCategory] = {}  # Store categories by name
        self.data_filename = "skills_data.json"  # Define default filename

    def add_category(self, category_name: str):
        """Adds a new skill category."""
        if category_name in self.categories:
            st.warning(f"Warning: Category '{category_name}' already exists.")
            return
        self.categories[category_name] = SkillCategory(category_name)
        st.success(f"Category '{category_name}' added.")
        self.save_data()  # Save data after adding category

    def get_category(self, category_name: str) -> SkillCategory | None:
        """Retrieves a skill category by name."""
        return self.categories.get(category_name)

    def remove_category(self, category_name: str):
        """Removes a skill category."""
        if category_name in self.categories:
            del self.categories[category_name]
            st.success(f"Category '{category_name}' removed.")
            self.save_data()  # Save data after removing category
        else:
            st.error(f"Error: Category '{category_name}' not found.")

    def display_all_skills(self):
        """Displays all skills across all categories."""
        if not self.categories:
            st.info("No skill categories defined yet.")
            return
        st.header("All Skills Overview")
        for category in self.categories.values():
            category.display_category_skills()
            st.markdown("---")  # Separator between categories

    # --- Persistence (Simplified to JSON) ---
    def save_data(self):
        """Saves all skill data to a JSON file."""
        data = {name: category.to_dict() for name, category in self.categories.items()}
        try:
            with open(self.data_filename, 'w') as f:
                json.dump(data, f, indent=4)
            st.success(f"Skill data saved to {self.data_filename}")
        except IOError as e:
            st.error(f"Error saving data: {e}")

    def load_data(self):
        """Loads skill data from a JSON file."""
        if not os.path.exists(self.data_filename):
            st.info(f"No data file found at {self.data_filename}. Starting fresh.")
            return
        try:
            with open(self.data_filename, 'r') as f:
                data = json.load(f)
            self.categories = {}  # Clear existing data
            for cat_name, cat_data in data.items():
                category = SkillCategory(cat_name)
                for skill_data in cat_data["skills"]:
                    skill_type = skill_data.pop("type")  # Get the skill type
                    if skill_type == "SoftSkill":
                        skill = SoftSkill(**skill_data)
                    elif skill_type == "HardSkill":
                        skill = HardSkill(**skill_data)
                    else:
                        st.warning(
                            f"Warning: Unknown skill type '{skill_type}' for skill '{skill_data['name']}'. Skipping.")
                        continue
                    category.add_skill(skill)
                self.categories[cat_name] = category
            st.success(f"Skill data loaded from {self.data_filename}")
        except json.JSONDecodeError as e:
            st.error(f"Error decoding JSON from {self.data_filename}: {e}")
        except IOError as e:
            st.error(f"Error loading data: {e}")

    # --- Placeholder for Export Functionality ---
    def export_as_pdf(self):
        """
        Placeholder for PDF export functionality.
        In a real application, you would use a library like ReportLab or FPDF2.
        """
        st.info(f"Generating a PDF report for your skills and saving to 'skills_report.pdf' (conceptual)...")
        st.write("This would involve iterating through all skills and categories,")
        st.write("formatting them, and using a PDF generation library.")
        st.write("Example: using ReportLab to draw text, shapes for mana bars, and tree structures for XP.")
        st.success("PDF export complete (conceptually).")

    def export_to_notion(self):
        """
        Placeholder for Notion embed functionality.
        In a real application, you would use the Notion API.
        """
        st.info(f"Connecting to Notion API to create/update a page or database (conceptual)...")
        st.write("This would involve authenticating with Notion, structuring your skill data,")
        st.write("and sending requests to create blocks or database entries.")
        st.write("Example: using the 'notion-client' library to add skills as database items.")
        st.success("Notion export complete (conceptually).")

    # --- Placeholder for Auto-Suggestion Functionality ---
    def auto_suggest_skills_github(self, github_username: str):
        """
        Placeholder for auto-suggesting skills based on GitHub activity.
        Requires GitHub API integration.
        """
        st.info(f"Auto-suggesting skills from GitHub for '{github_username}' (conceptual)...")
        st.write("Connecting to GitHub API to fetch repositories, languages, and commit history...")
        st.write("This would involve using a library like 'requests' to call GitHub's REST API,")
        st.write("parsing the response to identify frequently used languages, frameworks, or topics,")
        st.write("and suggesting them as new skills or updates to existing ones.")
        st.success("GitHub auto-suggestion complete (conceptually).")

    def auto_suggest_skills_vscode(self, vscode_usage_data_path: str):
        """
        Placeholder for auto-suggesting skills based on VSCode usage.
        This would typically involve parsing local VSCode telemetry or extension data.
        """
        st.info(f"Auto-suggesting skills from VSCode usage data (conceptual)...")
        st.write(f"Attempting to parse VSCode usage data from '{vscode_usage_data_path}'...")
        st.write("This would involve understanding the structure of VSCode's internal data files,")
        st.write("parsing them to identify frequently used extensions, languages, or commands,")
        st.write("and suggesting relevant skills.")
        st.warning("Note: Accessing VSCode internal data directly might be complex and platform-dependent.")
        st.success("VSCode auto-suggestion complete (conceptually).")

    def auto_suggest_skills_stackoverflow(self, stackoverflow_user_id: str):
        """
        Placeholder for auto-suggesting skills based on Stack Overflow history.
        Requires Stack Overflow API integration.
        """
        st.info(f"Auto-suggesting skills from Stack Overflow for user ID '{stackoverflow_user_id}' (conceptual)...")
        st.write("Connecting to Stack Overflow API to fetch user's questions, answers, and tags...")
        st.write("This would involve using a library like 'requests' to call Stack Overflow's API,")
        st.write("parsing the response to identify frequently used tags, accepted answers, or badges,")
        st.write("and suggesting them as new skills.")
        st.success("Stack Overflow auto-suggestion complete (conceptually).")


# --- Streamlit Application ---

def streamlit_app():
    st.set_page_config(layout="wide", page_title="Skill Management Platform")

    st.title("Skill Management Platform")
    st.markdown("Organize your skills with visual metaphors and track your progress!")

    # Initialize SkillPlatformManager in session state if not already present
    if 'manager' not in st.session_state:
        st.session_state.manager = SkillPlatformManager()
        st.session_state.manager.load_data()  # Load data on initial startup

    manager = st.session_state.manager

    # Sidebar for navigation
    st.sidebar.header("Actions")
    action = st.sidebar.radio(
        "Choose an action:",
        ("View All Skills", "Add Category", "Add Skill", "Update Skill Level",
         "Remove Skill", "Remove Category", "Export Skills", "Auto-Suggest Skills")
    )

    # Main content area based on selected action
    if action == "View All Skills":
        manager.display_all_skills()

    elif action == "Add Category":
        st.header("Add New Skill Category")
        with st.form("add_category_form"):
            cat_name = st.text_input("Category Name", key="add_cat_name")
            submitted = st.form_submit_button("Add Category")
            if submitted and cat_name:
                manager.add_category(cat_name)
            elif submitted and not cat_name:
                st.warning("Please enter a category name.")

    elif action == "Add Skill":
        st.header("Add New Skill to Category")
        category_names = list(manager.categories.keys())
        if not category_names:
            st.warning("Please add a skill category first.")
        else:
            with st.form("add_skill_form"):
                selected_cat = st.selectbox("Select Category", category_names, key="add_skill_cat")
                skill_name = st.text_input("Skill Name", key="add_skill_name")
                skill_type = st.radio("Skill Type", ("Soft Skill", "Hard Skill"), key="add_skill_type")
                skill_desc = st.text_area("Description (optional)", key="add_skill_desc")
                skill_level = st.slider("Initial Level", 0, 100, 0, key="add_skill_level")

                submitted = st.form_submit_button("Add Skill")
                if submitted and skill_name:
                    category = manager.get_category(selected_cat)
                    if category:
                        try:
                            if skill_type == 'Soft Skill':
                                skill = SoftSkill(skill_name, skill_level, skill_desc)
                            elif skill_type == 'Hard Skill':
                                skill = HardSkill(skill_name, skill_level, skill_desc)
                            category.add_skill(skill)
                            manager.save_data()  # Save after adding skill
                        except ValueError as e:
                            st.error(f"Error: {e}")
                elif submitted and not skill_name:
                    st.warning("Please enter a skill name.")

    elif action == "Update Skill Level":
        st.header("Update Skill Level")
        category_names = list(manager.categories.keys())
        if not category_names:
            st.warning("No categories available to update skills.")
        else:
            with st.form("update_skill_form"):
                selected_cat = st.selectbox("Select Category", category_names, key="update_skill_cat")

                # Get skills for the selected category dynamically
                current_category = manager.get_category(selected_cat)
                skill_names_in_cat = list(current_category.skills.keys()) if current_category else []

                if not skill_names_in_cat:
                    st.warning(f"No skills in '{selected_cat}' category.")
                else:
                    selected_skill = st.selectbox("Select Skill", skill_names_in_cat, key="update_skill_name")

                    if selected_skill:
                        skill_obj = current_category.get_skill(selected_skill)
                        if skill_obj:
                            new_level = st.slider(f"New Level for '{selected_skill}'", 0, 100, skill_obj.level,
                                                  key="update_skill_level")
                            submitted = st.form_submit_button("Update Level")
                            if submitted:
                                skill_obj.update_level(new_level)
                                manager.save_data()  # Save after updating skill
                        else:
                            st.error("Selected skill not found (this should not happen).")
                    else:
                        st.warning("Please select a skill to update.")

    elif action == "Remove Skill":
        st.header("Remove Skill from Category")
        category_names = list(manager.categories.keys())
        if not category_names:
            st.warning("No categories available to remove skills from.")
        else:
            with st.form("remove_skill_form"):
                selected_cat = st.selectbox("Select Category", category_names, key="remove_skill_cat")

                # Get skills for the selected category dynamically
                current_category = manager.get_category(selected_cat)
                skill_names_in_cat = list(current_category.skills.keys()) if current_category else []

                if not skill_names_in_cat:
                    st.warning(f"No skills in '{selected_cat}' category to remove.")
                else:
                    selected_skill = st.selectbox("Select Skill to Remove", skill_names_in_cat, key="remove_skill_name")
                    submitted = st.form_submit_button("Remove Skill")
                    if submitted and selected_skill:
                        manager.get_category(selected_cat).remove_skill(selected_skill)
                        manager.save_data()  # Save after removing skill
                    elif submitted and not selected_skill:
                        st.warning("Please select a skill to remove.")

    elif action == "Remove Category":
        st.header("Remove Skill Category")
        category_names = list(manager.categories.keys())
        if not category_names:
            st.warning("No categories available to remove.")
        else:
            with st.form("remove_category_form"):
                selected_cat = st.selectbox("Select Category to Remove", category_names, key="remove_cat_name")
                submitted = st.form_submit_button("Remove Category")
                if submitted and selected_cat:
                    manager.remove_category(selected_cat)
                elif submitted and not selected_cat:
                    st.warning("Please select a category to remove.")

    elif action == "Export Skills":
        st.header("Export Skills")
        export_choice = st.radio("Choose Export Format:", ("PDF (Conceptual)", "Notion (Conceptual)"))
        if st.button("Export"):
            if export_choice == "PDF (Conceptual)":
                manager.export_as_pdf()
            elif export_choice == "Notion (Conceptual)":
                manager.export_to_notion()

    elif action == "Auto-Suggest Skills":
        st.header("Auto-Suggest Skills")
        suggest_choice = st.radio("Suggest from:",
                                  ("GitHub (Conceptual)", "VSCode (Conceptual)", "Stack Overflow (Conceptual)"))

        if suggest_choice == "GitHub (Conceptual)":
            github_username = st.text_input("GitHub Username", key="github_username")
            if st.button("Suggest from GitHub"):
                if github_username:
                    manager.auto_suggest_skills_github(github_username)
                else:
                    st.warning("Please enter a GitHub username.")
        elif suggest_choice == "VSCode (Conceptual)":
            vscode_path = st.text_input("VSCode Usage Data Path (Conceptual)", key="vscode_path")
            if st.button("Suggest from VSCode"):
                if vscode_path:
                    manager.auto_suggest_skills_vscode(vscode_path)
                else:
                    st.warning("Please enter a VSCode usage data path.")
        elif suggest_choice == "Stack Overflow (Conceptual)":
            stackoverflow_id = st.text_input("Stack Overflow User ID", key="stackoverflow_id")
            if st.button("Suggest from Stack Overflow"):
                if stackoverflow_id:
                    manager.auto_suggest_skills_stackoverflow(stackoverflow_id)
                else:
                    st.warning("Please enter a Stack Overflow User ID.")


# Run the Streamlit app
if __name__ == "__main__":
    streamlit_app()