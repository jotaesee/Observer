export const appState = $state({
  selected_server: null,
  selected_section: "instances",
  isNewInstanceModalOpen: false,

  select_server(id) {
    this.selected_server = id;
    this.selected_section = "dashboard";
  },

  select_section(section) {
    this.selected_section = section;
  },

  go_home() {
    this.selected_server = null;
    this.selected_section = "instances";
  },

  toggle_Modal() {
    this.isNewInstanceModalOpen = !this.isNewInstanceModalOpen;
  },
});
