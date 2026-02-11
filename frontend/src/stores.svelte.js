export const appState = $state({
  selected_server: "null",
  selected_section: null,

  select_server(id) {
    this.selected_server = id;
  },

  select_section(section) {
    this.selected_section = section;
  },

  go_home() {
    this.selected_server = null;
  },
});
