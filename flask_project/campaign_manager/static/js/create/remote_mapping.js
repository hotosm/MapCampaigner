var remoteMap = null;
var addedLayers = {};

$.each(remote_projects_list, function (index, value) {
    addProject(' ', value)
});

setTimeout(function () {
    remoteMap = L.map('remote-map', {
        center: [0, 0],
        zoom: 2
    });
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© <a href="http://www.openstreetmap.org" target="_parent">OpenStreetMap</a> and ' +
        'contributors, under an <a href="http://www.openstreetmap.org/copyright" target="_parent">open license</a>',
        maxZoom: 18
    }).addTo(remoteMap);
    remoteMap.invalidateSize();
}, 100);

$('#search-projects-button').click(function () {
    var searchText = $('#sp-text-search').val();
    var organisationTag = $('#sp-organisation-tag').val();
    var campaignTag = $('#sp-campaign-tag').val();
    var mapperLevel = $('#sp-mapper-level :selected').val();
    var mappingTypes = $('#sp-mapping-types :selected').val();
    var pageNum = 1;
    searchProjects(pageNum, searchText, mapperLevel, mappingTypes, organisationTag, campaignTag);
});

function searchProjects(pageNum, searchText, mapperLevel, mappingTypes, organisationTag, campaignTag) {
    var url = '/search-remote?';
    var urlParams = '';

    urlParams += 'page=' + pageNum + '&';

    if(searchText) {
        urlParams += 'textSearch=' + searchText + '&';
    }

    if(mapperLevel) {
        urlParams += 'mapperLevel=' + mapperLevel + '&';
    }

    if(mappingTypes) {
        urlParams += 'mappingTypes=' + mappingTypes + '&';
    }

    if(organisationTag) {
        urlParams += 'organisationTag=' + organisationTag + '&';
    }

    if(campaignTag) {
        urlParams += 'campaignTag=' + campaignTag + '&';
    }

    url += urlParams;

    $.ajax({
        url: url,
        success: function (data) {
            var $listProjectsDiv = $('#list-projects');

            $listProjectsDiv.html('');

            try {
                data = JSON.parse(data);
            } catch (e) {
                $listProjectsDiv.html(data);
                return;
            }

            var results = data['results'];

            var nextButton = '';
            var prevButton = '';

            if(data['pagination']['pages'] > data['pagination']['page']) {
                var nextPage = parseInt(pageNum) + 1;
                nextButton = '<button type="button" class="btn btn-sm next-project-page" ' +
                    'onclick="searchProjects('+
                        nextPage + ',' +
                        (searchText ? '\''+searchText+'\'' : '\'\'') + ',' +
                        (mapperLevel ? '\''+mapperLevel+'\'' : '\'\'') + ',' +
                        (mappingTypes ? '\''+mappingTypes+'\'' : '\'\'') + ',' +
                        (organisationTag ? '\''+organisationTag+'\'' : '\'\'') + ',' +
                        (campaignTag ? '\''+campaignTag+'\'' : '\'\'') +')"> Next </button>'
            }

            if(data['pagination']['page'] - 1 > 0) {
                var prevPage = parseInt(pageNum) - 1;
                prevButton = '<button type="button" class="btn btn-sm prev-project-page" ' +
                    'onclick="searchProjects('+
                        prevPage + ',' +
                        (searchText ? '\''+searchText+'\'' : '\'\'') + ',' +
                        (mapperLevel ? '\''+mapperLevel+'\'' : '\'\'') + ',' +
                        (mappingTypes ? '\''+mappingTypes+'\'' : '\'\'') + ',' +
                        (organisationTag ? '\''+organisationTag+'\'' : '\'\'') + ',' +
                        (campaignTag ? '\''+campaignTag+'\'' : '\'\'') +')"> Prev </button>'
            }

            $listProjectsDiv.append(
                '<div style="margin-bottom:10px" class="pagination-projects"> Page ' + data['pagination']['page'] + ' / ' + data['pagination']['pages'] + '</div>'
            );

            $('.pagination-projects').append(nextButton);
            $('.pagination-projects').prepend(prevButton);

            $.each(results, function (index, result) {

                $('#list-projects').append(
                    '<div class="panel panel-default">'+
                    '<div class="panel-body project-detail" data-project-id="'+result['projectId']+'" id="list-'+result['projectId']+'">' +
                        '<a target="_blank" href="http://tm3.hotosm.org/project/'+result['projectId']+'"> #' + result['projectId'] + ' ' + result['name']+ '</a>' +
                        '<div class="grey-italic"> Mapped : '+ result['percentMapped']+'%, Validated : '+ result['percentValidated'] +'% </div>'+
                        '<div class="project-detail-desc">'+ result['shortDescription'] + '</div>' +
                        '<button type="button" class="btn btn-success btn-sm" onclick="addProject(this, '+result['projectId']+')">Add Project</button>' +
                    '</div>'+
                    '</div>'
                );

                if(typeof addedLayers[result['projectId']] !== 'undefined') {
                    $('#list-'+result['projectId']+' button').attr('disabled', true);
                }
            });
        }, error: function (data) {
            $('#list-projects').html('');
        }
    });
}

function addProject(el, projectId) {
    var url = '/project-detail?projectId=' + projectId;
    var $listAddedProjectsDiv = $('#list-added-projects');

    $.ajax({
        url: url,
        success: function (data) {
            try {
                data = JSON.parse(data);
            } catch (e) {
                return;
            }

            $(el).attr("disabled", true);
            var map = getMap();

            var layerGroup = L.geoJSON([data['tasks']], {
                style: function (feature) {
                    if(typeof taskStatusFillColor[feature.properties.taskStatus] !== 'undefined') {
                        return {
                            weight: 2,
                            color: "#999",
                            opacity: 1,
                            fillColor: taskStatusFillColor[feature.properties.taskStatus],
                            fillOpacity: 0.8
                        }
                    }
                    return feature.properties && feature.properties.style;
                },
                onEachFeature: function (feature, layer) {
                    var popupContent = feature.properties.taskStatus;
                    layer.bindPopup(popupContent);
                }
            });
            layerGroup.addTo(map);

            addedLayers[data['projectId']] = layerGroup;

            map.fitBounds(layerGroup.getBounds());

            if(Object.keys(addedLayers).length === 0) {
                $listAddedProjectsDiv.html('');
            }

            addedLayers[data['projectId']] = layerGroup;

            $listAddedProjectsDiv.append(
                '<div class="added-project well well-sm">'+
                    '<div class="project-detail-name" onclick="showProjectMap(this, '+data['projectId']+')">'+
                        '#'+data['projectId']+' '+data['projectInfo']['name']+''+
                    '</div>'+
                    '<div class="project-detail-desc">'+
                        data['projectInfo']['shortDescription']+
                    '</div>'+
                    '<div>'+
                        '<button type="button" class="btn btn-danger btn-sm" onclick="removeProject(this, '+data['projectId']+')" style="margin-top: 5px;">Remove</button>'+
                    '</div>'+
                '</div>'
            );

            if($listAddedProjectsDiv.find('#empty-list-remote-project').is(':visible')) {
                $('#empty-list-remote-project').hide();
            }
        }
    })
}

function removeProject(el, projectId) {
    var layer = addedLayers[projectId];
    var $listAddedProjectsDiv = $('#list-added-projects');
    var map = getMap();

    map.removeLayer(layer);

    delete addedLayers[projectId];
    $(el).parent().parent().remove();
    if(Object.keys(addedLayers).length === 0) {
        $('#empty-list-remote-project').show();
    }
}

function showProjectMap(el, projectId) {
    var layer = addedLayers[projectId];
    var map = getMap();

    map.fitBounds(layer.getBounds());
}

function getMap(){
    if (!remoteMap) {
        setTimeout(function(){getMap()},100);
    } else {
        return remoteMap
    }
}