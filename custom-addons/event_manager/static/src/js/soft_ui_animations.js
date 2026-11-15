/** @odoo-module **/

export function initSoftUIAnimations() {
    console.log("Chargement des animations Vanilla...");

    // ==================================================
    // DONNÉES FICTIVES (Septembre 2026)
    // ==================================================

    // Référence temporelle : Septembre 2026
    const currentDate = new Date('2026-09-07T08:00:00');

    // Structure des événements
    const eventsData = [
        {
            id: 1,
            name: "Gala de Charité",
            description: "Soirée de levée de fonds annuelle.",
            organizer: "Fondation Espoir",
            date: "2026-09-15",
            time: "19:00",
            location: "Hôtel de Ville",
            theme: "Solidarité",
            maxGuests: 200
        },
        {
            id: 2,
            name: "Conférence Tech AI",
            description: "Nouvelles avancées en IA.",
            organizer: "TechWorld",
            date: "2026-09-10",
            time: "09:00",
            location: "Centre des Congrès",
            theme: "Technologie",
            maxGuests: 150
        },
        {
            id: 3,
            name: "Lancement Produit X",
            description: "Présentation exclusive.",
            organizer: "InnovCorp",
            date: "2026-09-05",
            time: "18:00",
            location: "Espace Créatif",
            theme: "Business",
            maxGuests: 50
        },
        {
            id: 4,
            name: "Séminaire RH 2026",
            description: "Le futur du travail.",
            organizer: "HR Connect",
            date: "2026-09-22",
            time: "14:00",
            location: "Salle Horizon",
            theme: "Ressources Humaines",
            maxGuests: 100
        },
        {
            id: 5,
            name: "Atelier Design System",
            description: "Création de bibliothèques UI.",
            organizer: "Studio Dev",
            date: "2026-08-28", // Passé
            time: "10:00",
            location: "Campus Numérique",
            theme: "Design",
            maxGuests: 40
        }
    ];

    // Structure des invitations (Un invité + X accompagnants = total pour l'invitation)
    const invitationsData = [
        { eventId: 1, guest: "Invité A", arrivalTime: "18:50", companions: 1 },
        { eventId: 1, guest: "Invité B", arrivalTime: "19:05", companions: 0 },
        { eventId: 1, guest: "Invité C", arrivalTime: "18:45", companions: 3 },
        // Total event 1 artificiellement gonflé pour la démo
        { eventId: 2, guest: "Invité D", arrivalTime: "08:45", companions: 0 },
        { eventId: 2, guest: "Invité E", arrivalTime: "08:50", companions: 1 },
        { eventId: 3, guest: "Invité F", arrivalTime: "17:55", companions: 0 },
        { eventId: 4, guest: "Invité G", arrivalTime: "13:50", companions: 2 },
        { eventId: 5, guest: "Invité H", arrivalTime: "09:55", companions: 0 },
    ];

    // Données historiques pour le graphique d'évolution (Nb événements créés par mois en 2026)
    // Indices: 0=Avril, 1=Mai, 2=Juin, 3=Juillet, 4=Août, 5=Septembre
    const historicalEventsData = [
        { month: "Avril 2026", count: 2 },
        { month: "Mai 2026", count: 5 },
        { month: "Juin 2026", count: 3 },
        { month: "Juillet 2026", count: 1 },
        { month: "Août 2026", count: 4 },
        { month: "Septembre 2026", count: 8 }
    ];

    // ==================================================
    // LOGIQUE ET CALCULS
    // ==================================================

    // Variables calculées globales
    let enrichedEvents = [];
    let globalStats = {
        totalEvents: 0,
        upcomingEvents: 0,
        fullEvents: 0,
        totalCapacity: 0,
        totalRegistered: 0,
        globalFillRate: 0,
        totalGuests: 0,
        totalCompanions: 0
    };

    /**
     * Prépare et consolide les données (Jointure Evénements / Invitations)
     */
    function prepareData() {
        enrichedEvents = eventsData.map(event => {
            // Pour des données plus réalistes dans la démo, on simule des inscrits massifs
            // basés sur l'ID pour avoir des cas de figures variés (complets, presque, peu).
            let simulatedRegistered = 0;
            let guestsCount = 0;
            let companionsCount = 0;

            if (event.id === 1) { simulatedRegistered = 195; guestsCount = 100; companionsCount = 95; } // 97.5% - Presque complet
            else if (event.id === 2) { simulatedRegistered = 150; guestsCount = 100; companionsCount = 50; } // 100% - Complet
            else if (event.id === 3) { simulatedRegistered = 50; guestsCount = 30; companionsCount = 20; } // 100% - Complet
            else if (event.id === 4) { simulatedRegistered = 15; guestsCount = 10; companionsCount = 5; } // 15% - Peu
            else if (event.id === 5) { simulatedRegistered = 35; guestsCount = 20; companionsCount = 15; } // 87.5% - Passé, presque complet

            const totalRegistered = simulatedRegistered;
            const fillRate = Math.round((totalRegistered / event.maxGuests) * 100);

            return {
                ...event,
                totalRegistered,
                fillRate,
                guestsCount,
                companionsCount,
                isUpcoming: new Date(event.date) >= currentDate,
                isFull: fillRate >= 100
            };
        });

        calculateGlobalStatistics();
    }

    /**
     * Calcule les statistiques globales
     */
    function calculateGlobalStatistics() {
        globalStats.totalEvents = enrichedEvents.length;

        enrichedEvents.forEach(ev => {
            if (ev.isUpcoming) globalStats.upcomingEvents++;
            if (ev.isFull) globalStats.fullEvents++;
            globalStats.totalCapacity += ev.maxGuests;
            globalStats.totalRegistered += ev.totalRegistered;
            globalStats.totalGuests += ev.guestsCount;
            globalStats.totalCompanions += ev.companionsCount;
        });

        globalStats.globalFillRate = globalStats.totalCapacity > 0
            ? Math.round((globalStats.totalRegistered / globalStats.totalCapacity) * 100)
            : 0;
    }

    // ==================================================
    // MISES À JOUR DU DOM
    // ==================================================

    function updateStatCards() {
        document.getElementById('stat-total-events').textContent = globalStats.totalEvents;
        document.getElementById('stat-upcoming-events').textContent = globalStats.upcomingEvents;
        document.getElementById('stat-full-events').textContent = globalStats.fullEvents;
        document.getElementById('stat-global-rate').textContent = globalStats.globalFillRate + '%';
    }

    function updateFillRates() {
        // Trier par taux de remplissage décroissant
        const sortedEvents = [...enrichedEvents].sort((a, b) => b.fillRate - a.fillRate).slice(0, 4);

        const items = document.querySelectorAll('.fill-rate-item');
        items.forEach((item, index) => {
            if (sortedEvents[index]) {
                const ev = sortedEvents[index];
                item.querySelector('.event-name').textContent = ev.name;
                item.querySelector('.fill-rate-value').textContent = ev.fillRate + '%';

                // Animation différée pour la barre de progression
                setTimeout(() => {
                    item.querySelector('.progress-bar__value').style.width = ev.fillRate + '%';
                }, 100);
            } else {
                item.style.display = 'none'; // Cacher si pas assez de données
            }
        });
    }

    function updateRecentEvents() {
        // Trier du plus récent au plus ancien (basé sur la date)
        const recent = [...enrichedEvents].sort((a, b) => new Date(b.date) - new Date(a.date)).slice(0, 5);

        const rows = document.querySelectorAll('#recent-events-tbody tr');
        rows.forEach((row, index) => {
            if (recent[index]) {
                const ev = recent[index];

                // Formater la date manuellement pour l'affichage (ex: 15 Sept 2026)
                const dateObj = new Date(ev.date);
                const formattedDate = dateObj.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' });

                row.querySelector('.td-name').textContent = ev.name;
                row.querySelector('.td-date').textContent = formattedDate;
                row.querySelector('.td-time').textContent = ev.time;
                row.querySelector('.td-location').textContent = ev.location;
                row.querySelector('.td-organizer').textContent = ev.organizer;
                row.querySelector('.td-registered').textContent = `${ev.totalRegistered} / ${ev.maxGuests}`;
            } else {
                row.style.display = 'none';
            }
        });
    }

    function updateParticipantsDistribution() {
        const total = globalStats.totalGuests + globalStats.totalCompanions;
        const guestPercentage = total > 0 ? Math.round((globalStats.totalGuests / total) * 100) : 0;

        // Met à jour les libellés
        document.getElementById('count-guests').textContent = globalStats.totalGuests;
        document.getElementById('count-companions').textContent = globalStats.totalCompanions;

        // Met à jour la variable CSS pour le graphique (conic-gradient)
        const donut = document.getElementById('distribution-donut');
        donut.style.setProperty('--portion', `${guestPercentage}%`);
    }

    function updateAlerts() {
        // Filtres
        const full = enrichedEvents.filter(e => e.isFull).map(e => e.name);
        const almostFull = enrichedEvents.filter(e => e.fillRate >= 80 && e.fillRate < 100).map(e => e.name);
        const low = enrichedEvents.filter(e => e.fillRate < 30).map(e => e.name);

        // Injection (utilise un fallback si vide)
        document.getElementById('alert-full-events').textContent = full.length > 0 ? full.join(', ') : "Aucun événement.";
        document.getElementById('alert-almost-events').textContent = almostFull.length > 0 ? almostFull.join(', ') : "Aucun événement.";
        document.getElementById('alert-low-events').textContent = low.length > 0 ? low.join(', ') : "Aucun événement.";
    }

    function updateEventsEvolution() {
        // Trouver le maximum pour échelonner les barres
        const maxCount = Math.max(...historicalEventsData.map(d => d.count));

        const barGroups = document.querySelectorAll('#evolution-bars .bar-group');

        historicalEventsData.forEach((data, index) => {
            if (barGroups[index]) {
                const heightPercentage = (data.count / maxCount) * 100;
                const barFill = barGroups[index].querySelector('.bar-fill');

                setTimeout(() => {
                    barFill.style.height = `${heightPercentage}%`;
                }, 200 + (index * 100)); // Effet cascade
            }
        });

        // Mettre à jour le récapitulatif
        updateEvolutionSummary(maxCount);
    }

    function updateEvolutionSummary(maxCount) {
        // Période la plus active
        const maxPeriod = historicalEventsData.find(d => d.count === maxCount);

        // Minimum
        const minCount = Math.min(...historicalEventsData.map(d => d.count));
        const minPeriod = historicalEventsData.find(d => d.count === minCount);

        // Tendance (Septembre vs Août)
        const septData = historicalEventsData[5].count;
        const augData = historicalEventsData[4].count;

        let trendText = "";
        if (augData > 0) {
            const evolution = Math.round(((septData - augData) / augData) * 100);
            const sign = evolution >= 0 ? "+" : "";
            trendText = `${sign}${evolution} % en Septembre 2026 par rapport à Août 2026`;
        } else {
            trendText = "Données précédentes insuffisantes";
        }

        // Injection DOM
        document.getElementById('summary-active-period').textContent = maxPeriod.month;
        document.getElementById('summary-max').textContent = `${maxCount} événements — ${maxPeriod.month}`;
        document.getElementById('summary-min').textContent = `${minCount} événements — ${minPeriod.month}`;
        document.getElementById('summary-trend').textContent = trendText;
    }

    // ==================================================
    // INITIALISATION
    // ==================================================

    function initializeDashboard() {
        prepareData();

        // Appels des mises à jour visuelles
        updateStatCards();
        updateFillRates();
        updateRecentEvents();
        updateParticipantsDistribution();
        updateAlerts();
        updateEventsEvolution();
    }

    // Lancement au chargement du DOM
    document.addEventListener('DOMContentLoaded', initializeDashboard);
}