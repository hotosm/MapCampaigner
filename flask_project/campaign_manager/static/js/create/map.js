var campaignMap = L.map('campaign-map');
var drawnItems = new L.geoJSON();
var error_format_before = false;


// Add search control
var controlSearch = campaignMap.addControl( new L.Control.Search({
    url: 'https://nominatim.openstreetmap.org/search?format=json&q={s}',
    jsonpParam: 'json_callback',
    propertyName: 'display_name',
    propertyLoc: ['lat','lon'],
    marker: L.circleMarker([0,0],{radius:10}),
    autoCollapse: true,
    autoType: false,
    minLength: 2,
    zoom: 15
}));


L.tileLayer(map_provider, {
    attribution: '© <a href="http://www.openstreetmap.org" target="_parent">OpenStreetMap</a> and ' +
    'contributors, under an <a href="http://www.openstreetmap.org/copyright" target="_parent">open license</a>',
    maxZoom: 18
}).addTo(campaignMap);

function mapFitBound() {
    var bounds = [
        [-34.053726, 20.411482],
        [-34.009483, 20.467358]
    ];
    campaignMap.fitBounds(bounds);
}

if ($("#geometry").val()) {
    drawnItems = L.geoJSON(
        $.parseJSON($("#geometry").val()), {
            style: function (feature) {
                var status = 'unassigned';

                if ('status' in feature.properties) {
                    status = feature.properties['status'];
                } else if ('date' in feature.properties) {
                    var layerDate = moment(feature.properties['date'], 'YYYY-MM-DD', true);
                    var remainingDays = layerDate.diff(moment(), 'days') + 1;
                    if (remainingDays <= 0) {
                        status='complete';
                    } else {
                        status='incomplete';
                    }
                    feature.properties['status'] = status;
                }

                if (typeof taskStatusFillColor[status] !== 'undefined') {
                    return {
                        weight: 2,
                        color: "#999",
                        opacity: 1,
                        fillColor: taskStatusFillColor[status],
                        fillOpacity: 0.8
                    }
                }
                return feature.properties && feature.properties.style;
            },
            onEachFeature: function (feature, layer) {
                layer.bindPopup(
                    '<div class="layer-popup">' +
                        '<div class="layer-popup-area">' +
                            'Area &nbsp;&nbsp;: ' + feature.properties.area +
                        '</div>'+
                        '<div class="layer-popup-team">' +
                            'Team &nbsp;: ' + feature.properties.team +
                        '</div>'+
                        '<div class="layer-popup-team">' +
                            'Status : ' + capitalizeFirstLetter(feature.properties.status) +
                        '</div>'+
                    '</div>'
                )
            }
        }
    );
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
    layer.setStyle({
        weight: 2,
        color: "#999",
        opacity: 1,
        fillColor: '#D3D3D3',
        fillOpacity: 0.8
    });
    layer.bindPopup(
        '<div class="layer-popup">' +
            '<div class="layer-popup-area">' +
                'Area &nbsp;&nbsp;: -'+
            '</div>'+
            '<div class="layer-popup-team">' +
                'Team &nbsp;: -'+
            '</div>'+
            '<div class="layer-popup-team">' +
                'Status : Unassigned'+
            '</div>'+
        '</div>'
    );
    layer.closePopup();
    layer.openPopup();
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
    createCoverageTable();
    var geojson = drawnItems.toGeoJSON();
    $("#geometry").val(JSON.stringify(geojson));
    error_format_before = false
}

function clearCoverageTable() {
    $('.area-table-list').html('');
}

function createCoverageTable() {
    clearCoverageTable();
    $.each(drawnItems.getLayers(), function(index, layer) {
        var areaName = '';
        var teamName = '';
        var feature = '';
        var properties = '';
        var layerId = layer._leaflet_id;
        var status = '';

        feature = layer.feature = layer.feature || {};
        feature.type = feature.type || "Feature";
        properties = feature.properties = feature.properties || {};

        if(properties && 'team' in properties) {
            teamName = properties['team'];
        }

        if(properties && 'area' in properties) {
            if(properties['area']) {
                areaName = properties['area'];
            }
        }

        if(properties && 'status' in properties) {
            status = properties['status'];
        } else if(properties && 'date' in properties) {
            var propertyDate = properties['date'];
            if(propertyDate) {
                propertyDate = moment(propertyDate, 'YYYY-MM-DD', true);
                var remainingDays = propertyDate.diff(moment(), 'days') + 1;

                if (remainingDays <= 0) {
                    status='complete';
                } else {
                    status='incomplete';
                }
            }
        }

        $('.area-table-list').append(
            '<div class="row">'+
                '<input type="hidden" name="layer-index" value="'+layerId+'">'+
                '<div class="col-lg-4">'+
                    '<input onblur="updateGeometryString(this, \'area\', '+layerId+')" id="area_name-'+layerId+'" name="area_name" placeholder="Team Name" type="text" value="'+areaName+'" class="form-control area_name">'+
                '</div>'+
                '<div class="col-lg-4">'+
                    '<input onblur="updateGeometryString(this, \'team\', '+layerId+')" name="team_name" placeholder="Team Name" type="text" value="'+teamName+'" class="form-control">'+
                '</div>'+
                '<div class="col-lg-4">'+
                    '<select id="status-'+layerId+'" onchange="updateGeometryString(this, \'status\', '+layerId+')" class="form-control">'+
                          '<option value="unassigned" selected="selected">Unassigned</option>'+
                          '<option value="incomplete">Incomplete</option>'+
                          '<option value="complete">Complete</option>'+
                    '</select>'+
                '</div>'+
            '</div>'
        );

        if(status) {
            $("#status-"+layerId).val(status);
        }
    });
}

function updateGeometryString(el, property,  layerId) {
    var val = $(el).val();
    var layer = drawnItems.getLayer(layerId);
    layer.feature['properties'][property] = val;
    var geojson = drawnItems.toGeoJSON();
    $("#geometry").val(JSON.stringify(geojson));
    if(property === 'status') {
        layer.setStyle({
            opacity: 1,
            fillColor:taskStatusFillColor[val],
            fillOpacity: 0.8
        });
    }

    var area = layer.feature['properties']['area'] || '-';
    var team = layer.feature['properties']['team'] || '-';
    var status = layer.feature['properties']['status'] || 'unassigned';

    layer.bindPopup(
        '<div class="layer-popup">' +
            '<div class="layer-popup-area">' +
                'Area &nbsp;&nbsp;: ' + area +
            '</div>'+
            '<div class="layer-popup-team">' +
                'Team &nbsp;: ' + team +
            '</div>'+
            '<div class="layer-popup-team">' +
                'Status : ' + capitalizeFirstLetter(status) +
            '</div>'+
        '</div>'
    );
    layer.closePopup();
    layer.openPopup();
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