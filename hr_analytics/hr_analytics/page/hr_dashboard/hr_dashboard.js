frappe.pages["hr-dashboard"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "HR Dashboard",
		single_column: true,
	});
	new hr_analytics.Dashboard(page);
};

hr_analytics.Dashboard = class {
	constructor(page) {
		this.page = page;
		this.state = { screen: null, filters: {} };
		this.build_layout();
		this.build_filters();
		this.load_screens();
	}

	build_layout() {
		this.$body = $(`
			<div class="hra-shell">
				<div class="hra-sidebar"></div>
				<div class="hra-main">
					<div class="hra-toolbar"></div>
					<div class="hra-grid"></div>
				</div>
			</div>
		`).appendTo(this.page.body);
		this.$sidebar = this.$body.find(".hra-sidebar");
		this.$toolbar = this.$body.find(".hra-toolbar");
		this.$grid = this.$body.find(".hra-grid");
	}

	build_filters() {
		this.page.add_field({
			fieldtype: "Link",
			fieldname: "company",
			label: "Company",
			options: "Company",
			default: frappe.defaults.get_default("company"),
			change: () => this.on_filter_change(),
		});
		this.page.add_field({
			fieldtype: "Date",
			fieldname: "from_date",
			label: "From",
			change: () => this.on_filter_change(),
		});
		this.page.add_field({
			fieldtype: "Date",
			fieldname: "to_date",
			label: "To",
			change: () => this.on_filter_change(),
		});
		this.page.set_secondary_action("Refresh", () => this.load_screen(this.state.screen), "refresh-cw");
	}

	on_filter_change() {
		this.state.filters = {
			company: this.page.fields_dict.company.get_value(),
			from_date: this.page.fields_dict.from_date.get_value(),
			to_date: this.page.fields_dict.to_date.get_value(),
		};
		this.load_screen(this.state.screen);
	}

	load_screens() {
		frappe.call({ method: "hr_analytics.api.widgets.get_screens" }).then((r) => {
			this.screens = r.message || [];
			this.render_sidebar();
			if (this.screens.length) this.load_screen(this.screens[0].name);
		});
	}

	render_sidebar() {
		this.$sidebar.empty();
		this.screens.forEach((s) => {
			$(`<div class="hra-nav-item" data-screen="${s.name}">
				<i class="${s.icon || "ti ti-layout-dashboard"}"></i><span>${frappe.utils.escape_html(s.title)}</span>
			</div>`)
				.appendTo(this.$sidebar)
				.on("click", () => this.load_screen(s.name));
		});
	}

	load_screen(screen_name) {
		if (!screen_name) return;
		this.state.screen = screen_name;
		this.$sidebar.find(".hra-nav-item").removeClass("active");
		this.$sidebar.find(`[data-screen="${screen_name}"]`).addClass("active");
		this.$grid.html('<div class="text-muted hra-loading">Loading…</div>');

		frappe.call({
			method: "hr_analytics.api.widgets.get_widgets_for_screen",
			args: { screen: screen_name },
		}).then((r) => {
			const widgets = r.message || [];
			this.$grid.empty();
			widgets.forEach((w) => this.render_widget(w));
		});
	}

	render_widget(widget) {
		const span = widget.column_span || "1";
		const $card = $(`
			<div class="hra-card hra-span-${span}">
				<p class="hra-card-title">${frappe.utils.escape_html(widget.widget_name)}</p>
				${widget.description ? `<p class="hra-card-desc">${frappe.utils.escape_html(widget.description)}</p>` : ""}
				<div class="hra-card-body"><div class="text-muted">Loading…</div></div>
			</div>
		`).appendTo(this.$grid);
		const $body = $card.find(".hra-card-body");

		frappe.call({
			method: "hr_analytics.api.widgets.get_widget_data",
			args: { widget: widget.name, global_filters: JSON.stringify(this.state.filters) },
		}).then((r) => {
			hr_analytics.render(widget.widget_type, $body, r.message);
		}).catch(() => {
			$body.html('<div class="text-muted">Could not load this widget — check its config in Dashboard Widget.</div>');
		});
	}
};
