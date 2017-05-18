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
        clearButton: true,
        onSelect: function (fd, date) {
            if (date) {
                date_from = date.getTime();
            } else {
                date_from = '';
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
        clearButton: true,
        onSelect: function (fd, date) {
            if (date) {
                date_to = date.getTime();
            } else {
                date_to = '';
            }
        },
        todayButton: new Date()
    });


    if(captured_date_to) {
        $datepicker_to.data('datepicker')
            .selectDate(new Date(Number(captured_date_to)));
    }

    $('#refresh-with-date').click(function () {

        if((date_from && !date_to) ||
            (date_to && !date_from)) {
            alert('Empty date');
            return;
        }

        if(date_to && (date_to < date_from)) {
            alert('Invalid range');
            return;
        }

        var map = that.map || null;

        if(!map) {
            return;
        }

        var selected = $('#feature_select').val();
        var bounds = map.getBounds(),
            bbox = bounds.toBBoxString();

        var date_query = "";

        if(date_to && date_from) {
            date_query += '&date_from=' + date_from + '&date_to=' + date_to;
        }

        window.location = "?bbox=" + bbox
            + "&obj=" + selected
            + date_query
    });

});

