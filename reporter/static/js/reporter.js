var getObjectType = function(){
    return $($("#object_type option")[$("#object_type")
                                      .attr("selectedIndex")]).text().trim();
};

/* Update stats */
L.Control.UpdateStats = L.Control.extend({

    onAdd: function (map) {
        var className = 'leaflet-control-stats',
            container = L.DomUtil.create('div', className);

        var link = L.DomUtil.create('a', "", container);
        link.href = '#';
        link.title = "Get stats for this view";
        var fn = function (e) {
            var bounds = map.getBounds(),
                bbox = bounds.toBBoxString();
            window.location = "?bbox=" + bbox + "&obj=" + getObjectType();
        };

        L.DomEvent
            .on(link, 'click', L.DomEvent.stopPropagation)
            .on(link, 'click', L.DomEvent.preventDefault)
            .on(link, 'click', fn, map)
            .on(link, 'dblclick', L.DomEvent.stopPropagation);

        return container;
    }
});

L.Map.addInitHook(function () {
    if (this.options.updateStatsControl) {
        var options = this.options.statsControlOptions ? this.options.statsControlOptions : {};
        this.updateStatsControl = new L.Control.UpdateStats(this, options);
        this.addControl(this.updateStatsControl);
    }
});

