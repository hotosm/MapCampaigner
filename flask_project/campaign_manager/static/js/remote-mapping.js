var remoteMap = null;
var addedLayers = {};

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
    var url = 'http://tasking-manager-staging.eu-west-1.elasticbeanstalk.com/api/v1/project/search?';
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
            $('#list-projects').html('');
            var results = data['results'];
            $('#list-projects').append(
                '<div style="margin-bottom:10px"> Page ' + data['pagination']['page'] + ' / ' + data['pagination']['pages'] + '</div>'
            );
            $.each(results, function (index, result) {

                $('#list-projects').append(
                    '<div class="panel panel-default">'+
                    '<div class="panel-body project-detail" data-project-id="'+result['projectId']+'" id="list-'+result['projectId']+'">' +
                        '<a target="_blank" href="http://tasks.hotosm.org/project/'+result['projectId']+'"> #' + result['projectId'] + ' ' + result['name']+ '</a>' +
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
    var url = 'http://tasking-manager-staging.eu-west-1.elasticbeanstalk.com/api/v1/project/' + projectId;
    var $listAddedProjectsDiv = $('#list-added-projects');

    $.ajax({
        url: url,
        success: function (data) {
            $(el).attr("disabled", true);
            var map = getMap();

            var layerGroup = L.geoJSON();
            layerGroup.addTo(map);

            layerGroup.addData(data['tasks']);

            map.fitBounds(layerGroup.getBounds());

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
            )
        }
    })
}

function removeProject(el, projectId) {
    var layer = addedLayers[projectId];
    var map = getMap();

    map.removeLayer(layer);

    delete addedLayers[projectId];
    $(el).parent().parent().remove();
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