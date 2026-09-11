window.hr_analytics = window.hr_analytics || {};

hr_analytics.PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#6250d6", "#e34948", "#008300"];
hr_analytics.STATUS_COLOR = { good: "#0ca30c", warn: "#fab219", danger: "#d03b3b", neutral: "#888780" };

hr_analytics.render = function (widget_type, $el, data) {
	$el.empty();
	if (data == null) {
		$el.html('<div class="text-muted">No data</div>');
		return;
	}
	switch (widget_type) {
		case "Number Card":
			return hr_analytics.render_number_card($el, data);
		case "Bar Chart":
			return hr_analytics.render_bar($el, data);
		case "Donut Chart":
			return hr_analytics.render_donut($el, data);
		case "Line Chart":
			return hr_analytics.render_bar($el, data); // same renderer, vertical bars read fine as a trend too
		case "Workflow Timeline":
			return hr_analytics.render_workflow_timeline($el, data);
		case "Table":
			return hr_analytics.render_table($el, data);
		default:
			$el.html('<div class="text-muted">Unsupported widget type</div>');
	}
};

hr_analytics.render_number_card = function ($el, data) {
	const value = typeof data === "object" ? data.value : data;
	$el.html(`<p class="hra-number">${frappe.utils.escape_html(String(value ?? "—"))}</p>`);
};

hr_analytics.render_bar = function ($el, rows) {
	if (!rows || !rows.length) return $el.html('<div class="text-muted">No data</div>');

	// Detect single-series ({label,value}) vs multi-series ({label, seriesA, seriesB, ...})
	const keys = Object.keys(rows[0]).filter((k) => k !== "label");
	const seriesKeys = keys.length ? keys : ["value"];
	const max = Math.max(...rows.flatMap((r) => seriesKeys.map((k) => Number(r[k]) || 0)), 1);

	if (seriesKeys.length > 1) {
		const legend = seriesKeys
			.map((k, i) => `<span class="hra-legend-item"><span class="hra-swatch" style="background:${hr_analytics.PALETTE[i]}"></span>${frappe.utils.escape_html(k)}</span>`)
			.join("");
		$el.append(`<div class="hra-legend">${legend}</div>`);
	}

	const $chart = $('<div class="hra-bar-chart"></div>').appendTo($el);
	rows.forEach((r) => {
		const $group = $('<div class="hra-bar-group"></div>').appendTo($chart);
		const $bars = $('<div class="hra-bar-bars"></div>').appendTo($group);
		seriesKeys.forEach((k, i) => {
			const v = Number(r[k]) || 0;
			const pct = Math.max((v / max) * 100, 2);
			$(`<div class="hra-bar" style="height:${pct}%;background:${hr_analytics.PALETTE[i]}" title="${frappe.utils.escape_html(k)}: ${v}"></div>`).appendTo($bars);
		});
		$(`<p class="hra-bar-label">${frappe.utils.escape_html(String(r.label))}</p>`).appendTo($group);
	});
};

hr_analytics.render_donut = function ($el, rows) {
	if (!rows || !rows.length) return $el.html('<div class="text-muted">No data</div>');
	const total = rows.reduce((s, r) => s + (Number(r.value) || 0), 0) || 1;
	let acc = 0;
	const stops = rows
		.map((r, i) => {
			const start = (acc / total) * 100;
			acc += Number(r.value) || 0;
			const end = (acc / total) * 100;
			return `${hr_analytics.PALETTE[i % hr_analytics.PALETTE.length]} ${start}% ${end}%`;
		})
		.join(", ");

	$el.append(`<div class="hra-donut-wrap"><div class="hra-donut" style="background:conic-gradient(${stops})"><div class="hra-donut-hole"></div></div></div>`);
	const legend = rows
		.map((r, i) => {
			const pct = Math.round(((Number(r.value) || 0) / total) * 100);
			return `<span class="hra-legend-item"><span class="hra-swatch" style="background:${hr_analytics.PALETTE[i % hr_analytics.PALETTE.length]}"></span>${frappe.utils.escape_html(String(r.label))} ${pct}%</span>`;
		})
		.join("");
	$el.append(`<div class="hra-legend">${legend}</div>`);
};

hr_analytics.render_workflow_timeline = function ($el, data) {
	if (!data || !data.states || !data.states.length) {
		return $el.html(`<div class="text-muted">${frappe.utils.escape_html(data && data.message ? data.message : "No workflow configured on this doctype")}</div>`);
	}
	const $row = $('<div class="hra-timeline"></div>').appendTo($el);
	data.states.forEach((s, i) => {
		const $step = $(`
			<div class="hra-timeline-step">
				<div class="hra-timeline-count">${s.count}</div>
				<p class="hra-timeline-label">${frappe.utils.escape_html(s.state)}</p>
			</div>
		`).appendTo($row);
		if (i < data.states.length - 1) $('<div class="hra-timeline-connector"></div>').appendTo($row);
	});
};

hr_analytics.render_table = function ($el, rows) {
	if (!rows || !rows.length) return $el.html('<div class="text-muted">No data</div>');
	const cols = Object.keys(rows[0]).filter((k) => k !== "name");
	let html = '<table class="hra-table"><thead><tr>';
	cols.forEach((c) => (html += `<th>${frappe.utils.escape_html(c)}</th>`));
	html += "</tr></thead><tbody>";
	rows.forEach((r) => {
		html += "<tr>";
		cols.forEach((c) => {
			let cell = r[c];
			let cls = "";
			if (c === "status") {
				cls = cell === "Overdue" ? "hra-badge-danger" : cell === "Due soon" ? "hra-badge-warn" : "hra-badge-good";
				cell = `<span class="hra-badge ${cls}">${frappe.utils.escape_html(String(cell))}</span>`;
			} else {
				cell = frappe.utils.escape_html(String(cell ?? ""));
			}
			html += `<td>${cell}</td>`;
		});
		html += "</tr>";
	});
	html += "</tbody></table>";
	$el.html(html);
};
