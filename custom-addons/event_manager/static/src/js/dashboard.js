/** @odoo-module **/

import { Component, onWillStart, onMounted, onWillUnmount, useRef, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadBundle } from "@web/core/assets";

export class EventDashboard extends Component {
    static template = "event_manager.EventDashboard";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.chartCanvasRef = useRef("chartCanvas");
        this.chartInstance = null;

        this.state = useState({
            count_all_events: 0,
            percentage_of_created_events_last_7_days: 0,
            count_upcoming_events: 0,
            count_events_of_this_month: 0,
            percentage_of_events_this_month: 0,
            percentage_of_events_fully_booked: 0,
            chart_labels: [],
            chart_values: [],
            max_period: null,
            min_period: null,
            max_guest_period: null,
            list_of_last_created_events: [],
        });

        // 1. Précharger la bibliothèque Chart.js avant le rendu du composant
        onWillStart(async () => {
            const result = await this.orm.call(
                "fiesta.event.dashboard",
                "get_tiles_data",
                [],
                {}
            );

            this.state.count_all_events = result.count_all_events || 0;
            this.state.percentage_of_created_events_last_7_days = result.percentage_of_created_events_last_7_days || 0;
            this.state.count_upcoming_events = result.count_upcoming_events || 0;
            this.state.count_events_of_this_month = result.count_events_of_this_month || 0;
            this.state.percentage_of_events_this_month = result.percentage_of_events_this_month || 0;
            this.state.percentage_of_events_fully_booked = result.percentage_of_events_fully_booked || 0;
            this.state.chart_labels = result.chart_labels || [];
            this.state.chart_values = result.chart_values || [];
            this.state.max_period = result.max_period || null;
            this.state.min_period = result.min_period || null;
            this.state.max_guest_period = result.max_guest_period || null;
            this.state.list_of_last_created_events = result.list_of_last_created_events || [];
            await loadBundle("web.chartjs_lib");
        });
        // 2. Initialiser le graphique une fois le DOM prêt
        onMounted(() => {
            this.renderChart();
        })
        // 3. Détruire le graphique lorsque le composant est fermé/remplacé
        onWillUnmount(() => {
            if (this.chartInstance) {
                this.chartInstance.destroy();
            }
        })
    }

    openEvent(eventId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "fiesta.event",
            res_id: eventId,
            views: [[false, "form"]],
            target: "current",
        });
    }

    openAllEvents() {
        this.action.doAction("event_manager.action_fiesta_event_all");
    }

    renderChart() {
        if (!this.chartCanvasRef.el) {
            return;
        }
        if (this.chartInstance) {
            this.chartInstance.destroy();
        }
        const ctx = this.chartCanvasRef.el.getContext("2d");
        
        // "Chart" est maintenant disponible globalement
        this.chartInstance = new Chart(ctx, {
            type: "bar",
            data: {
                // Remplacement par vos variables d'état dynamiques
                labels: this.state.chart_labels, 
                datasets: [
                    {
                        label: "Événements organisés",
                        // Remplacement par vos variables d'état dynamiques
                        data: this.state.chart_values, 
                        backgroundColor: "#cb0c9f", 
                        borderRadius: 4,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false,
                    },
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            borderDash: [5, 5],
                        },
                    },
                    x: {
                        grid: {
                            display: false,
                        },
                    },
                },
            },
        });
    }
}

registry.category("actions").add(
    "event_dashboard_tag",
    EventDashboard
);