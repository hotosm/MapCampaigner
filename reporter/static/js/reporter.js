
/* Update stats */
L.Control.UpdateStats = L.Control.extend({

    onAdd: function (map) {
        var className = 'leaflet-control-stats',
            container = L.DomUtil.create('div', className),
            option,
            choice;

        L.DomEvent.disableClickPropagation(container);
        var div = L.DomUtil.create('div', "", container);
        var select = L.DomUtil.create('select', "", div);
        for (var i = 0, l = this.options.choices.length; i<l; i++) {
            option = L.DomUtil.create('option', "", select);
            choice = this.options.choices[i];
            option.value = option.innerHTML = choice;
            if (choice == this.options.selected) {
                option.selected = "selected";
            }
        }

        L.DomEvent
            .on(select, 'change', function (e) {
                map.updateStatsControl.options.selected = e.target.value;
            });

        var link = L.DomUtil.create('a', "", container);
        link.href = '#';
        link.innerHTML = "&nbsp;";
        link.title = "Get stats for this view";
        var fn = function (e) {
            var bounds = map.getBounds(),
                bbox = bounds.toBBoxString();
            window.location = "?bbox=" + bbox + "&obj=" + select.value;
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
        this.updateStatsControl = new L.Control.UpdateStats(options);
        this.addControl(this.updateStatsControl);
    }
});

$(function(){
    $('.view-hm').click(function(e){
        var username = $(this).attr("data-user");
        $.ajax("/user", {
            data: {username: username,
                bbox: window.bbox},
            success: function(data){
                if (window.hmlayer) {
                    window.map.removeLayer(window.hmlayer);
                }
                var heatmap = new L.TileLayer.HeatCanvas({},{'step':0.07, 'degree':HeatCanvas.LINEAR, 'opacity':0.7});
                $.each(data.d, function(i,e){
                    heatmap.pushData(e[0], e[1], 1);
                })
                window.map.addLayer(heatmap);
                window.hmlayer = heatmap;
            }
        });
    });

    $('.clear-hm').click(function(e){
        if (window.hmlayer) {
            window.map.removeLayer(window.hmlayer);
            delete window.hmlayer;
        }
    });

    // Set up detail row hiding etc.

    $('.details-toggle').click(function(e){
        var rowId = $(this).attr("value");
        $("#"+rowId).toggle();
    });
    $('#all-details').click(function(e){
        var status = $(this).attr("checked");
        if (status)
        {
            $(".details-row").show();
        }
        else
        {
            $(".details-row").hide();
        }
        $('.details-toggle').attr("checked", status);
    });

    var date_from = null;
    var date_to = null;
    var that = this;
    var current_url = window.location.href;

    var captured_date_from = /date_from=([^&]+)/.exec(current_url);
    if(captured_date_from && captured_date_from.length > 0) {
        captured_date_from = captured_date_from[1];
    }
    var captured_date_to = /date_to=([^&]+)/.exec(current_url);
    if(captured_date_to && captured_date_to.length > 0) {
        captured_date_to = captured_date_to[1];
    }
    var $datepicker_from = $('#date-from');
    var $datepicker_to = $('#date-to');

    $datepicker_from.datepicker({
        autoClose: true,
        onSelect: function (fd, date) {
            if (date) {
                date_from = date.getTime();
            }
        },
        todayButton: new Date()
    });

    if(captured_date_from) {
        $datepicker_from.data('datepicker')
            .selectDate(new Date(Number(captured_date_from)));
    }

    $datepicker_to.datepicker({
        autoClose: true,
        onSelect: function (fd, date) {
            if (date) {
                date_to = date.getTime();
            }
        },
        todayButton: new Date()
    });


    if(captured_date_to) {
        $datepicker_to.data('datepicker')
            .selectDate(new Date(Number(captured_date_to)));
    }

    $('#refresh-with-date').click(function () {
        if(!date_from || !date_to) {
            alert('Empty date');
            return;
        }

        if(date_to < date_from) {
            alert('Invalid range');
            return;
        }

        var map = that.map || null;

        if(!map) {
            return;
        }

        var selected = map.updateStatsControl.options.selected;
        var bounds = map.getBounds(),
            bbox = bounds.toBBoxString();
        window.location = "?bbox=" + bbox
            + "&obj=" + selected
            + "&date_from=" + date_from
            + "&date_to=" + date_to;
    });

});

