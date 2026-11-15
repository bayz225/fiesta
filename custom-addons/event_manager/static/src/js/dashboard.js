/** @odoo-module **/

import { Component, onWillStart, onMounted, onWillUnmount, useRef, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadBundle } from "@web/core/assets";

export class EventDashboard extends Component {
    static template = "event_manager.EventDashboard";

    setup() {
        this.orm = useService("orm");
        this.chartCanvasRef = useRef("chartCanvas");
        this.chartInstance = null;

        this.state = useState({
            allEventsCount: 0,
            allEventsLastWeekPercentage: 0,
            upcomingEventsCount: 0,
            thisMonthEventsPercentage: 0,
            allEventsFullyCount: 0,
            allEventsFullyPercentage: 0,
            chartLabels: [],
            chartValues: [],
            maxPeriod: null,
            minPeriod: null,
            maxGuestPeriod: null,
            lastEventsList: [],
        });

        // 1. Précharger la bibliothèque Chart.js avant le rendu du composant
        onWillStart(async () => {
            const result = await this.orm.call(
                "res.partner",
                "get_tiles_data",
                [],
                {}
            );

            this.state.allEventsCount = result.all_events_count || 0;
            this.state.allEventsLastWeekPercentage = result.all_events_last_week_percentage || 0;
            this.state.upcomingEventsCount = result.upcoming_events_count || 0;
            this.state.thisMonthEventsPercentage = result.this_month_events_percentage || 0;
            this.state.thisMonthEventsCount = result.this_month_events_count || 0;
            this.state.allEventsFullyPercentage = result.all_events_fully_percentage || 0;
            this.state.chartLabels = result.chart_labels || [];
            this.state.chartValues = result.chart_values || [];
            this.state.maxPeriod = result.max_period || null;
            this.state.minPeriod = result.min_period || null;
            this.state.maxGuestPeriod = result.max_guest_period || null;
            this.state.lastEventsList = result.last_events_list || [];
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
                labels: this.state.chartLabels, 
                datasets: [
                    {
                        label: "Événements organisés",
                        // Remplacement par vos variables d'état dynamiques
                        data: this.state.chartValues, 
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