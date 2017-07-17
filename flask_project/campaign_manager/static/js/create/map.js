var campaignMap = L.map('campaign-map');
var drawnItems = new L.geoJSON();

var bounds = [
    [-34.053726, 20.411482],
    [-34.009483, 20.467358]
];

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© <a href="http://www.openstreetmap.org" target="_parent">OpenStreetMap</a> and ' +
        'contributors, under an <a href="http://www.openstreetmap.org/copyright" target="_parent">open license</a>',
        maxZoom: 18
    }).addTo(campaignMap);

campaignMap.fitBounds(bounds);

if(google_api_key) {
    new L.Control.GPlaceAutocomplete({
        position: "topright",
        callback: function (location) {
            campaignMap.fitBounds([
                [
                    location.geometry.viewport.getSouthWest().lat(),
                    location.geometry.viewport.getSouthWest().lng()
                ],
                [
                    location.geometry.viewport.getNorthEast().lat(),
                    location.geometry.viewport.getNorthEast().lng()
                ]
            ]);
        }
    }).addTo(campaignMap);
}

if ($("#geometry").val()) {
    drawnItems = L.geoJSON($.parseJSON($("#geometry").val()));
    campaignMap.fitBounds(drawnItems.getBounds());
}
campaignMap.addLayer(drawnItems);

var drawControl = new L.Control.Draw({
    draw: {
        polyline: false,
        marker: false,
        circle: false
    },
    edit: {
        featureGroup: drawnItems
    },
    remove: {
        featureGroup: drawnItems
    }
}, this);

campaignMap.addControl(drawControl);
campaignMap.on('draw:created', saveLayer);
campaignMap.on('draw:edited', editLayer);
campaignMap.on('draw:deleted', deleteLayer);
campaignMap.on('draw:drawstart', startDraw);
campaignMap.on('draw:drawstop', stopDraw);

var temporaryDrawnLayers = null;

function saveLayer(e) {
    temporaryDrawnLayers = null;
    var layer = e.layer;
    drawnItems.addLayer(layer);
    getAreaSize();
    stringfyGeometry();
}

function editLayer(e) {
    var layers = e.layers;
    getAreaSize();
    stringfyGeometry();
}

function deleteLayer(e) {
    var layers = e.layers;
    layers.eachLayer(function (feature) {
        drawnItems.removeLayer(feature);
    });
    getAreaSize();
    stringfyGeometry();
}

function startDraw(e) {
    temporaryDrawnLayers = jQuery.extend(true, {}, drawnItems);
    drawnItems.clearLayers();
}

function stopDraw(e) {
    if (temporaryDrawnLayers !== null) {
        var temporaryLayers = temporaryDrawnLayers._layers;
        for (var key in temporaryLayers) {
            drawnItems.addLayer(temporaryLayers[key]);
        }
        temporaryDrawnLayers = null;
    }
}

function stringfyGeometry() {
    var json = drawnItems.toGeoJSON();
    $("#geometry").val(JSON.stringify(json));
}

function getAreaSize() {
    var totalAreaSize = 0;
    drawnItems.eachLayer(function (layer) {
        totalAreaSize += L.GeometryUtil.geodesicArea(layer.getLatLngs()[0]);
    });

    var kmSquare = parseFloat(totalAreaSize / 1000000);
    $('#campaign-map-area-size').html('Area size : ' + kmSquare.toFixed(2) + ' km<sup>2</sup>');
    if (totalAreaSize > maxAreaSize) {
        showNotifications('Area of the campaign is too big, please reduce the area.', 'danger');
        $('.map-wrapper').data('error', 'Area of the campaign is too big, please reduce the area.');
        $('#campaign-map-area-size').removeClass('label-success');
        $('#campaign-map-area-size').addClass('label-danger');
    } else {
        clearNotification();
        $('.map-wrapper').data('error', '');
        $('#campaign-map-area-size').removeClass('label-danger');
        $('#campaign-map-area-size').addClass('label-success');
    }
}

function getAOIMap() {
    return campaignMap;
}