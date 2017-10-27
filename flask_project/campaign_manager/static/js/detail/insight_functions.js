var activeInsightPanel = '';
var errorPanel = null;
var mapperEngagementChart = null;

function updateMapperEngagementTotal() {

    $('.user-engagement-loading').hide();
    $('#user-engagement-wrapper').show();

    if(contributors.length > 0) {
        $('#total-users-engaged').html(contributors.length);
        $('#contributors').html(contributors.length);
    } else {
        $('#user-engagement-wrapper').html('<div class="no-data" style="padding-top: 20px;"> No users contribution </div>');
        $('#user-engagement-wrapper').css({
            height: '80px'
        });
        $('#total-users-engaged').html(0);
        $('#contributors').html(0);
        return;
    }

    var chartDateOption = {
        elements: {
            line: {
                tension: 0.000001
            }
        },
        scales: {
            xAxes: [{
                type: 'time',
                time: {
                    displayFormats: {
                        'day': 'DD/MM',
                        'week': 'DD/MM',
                        'month': 'MM/YY',
                        'quarter': 'MM/YY',
                        'year': 'YY'
                    }
                }
            }]
        }
    };

    var frequencyOption = {
        maintainAspectRatio: true,
        elements: {
            line: {
                tension: 0.000001
            }
        },
        scales: {
            xAxes: [{
                type: 'time',
                time: {
                    displayFormats: {
                        'day': 'DD/MM',
                        'week': 'DD/MM',
                        'month': 'MM/YY',
                        'quarter': 'MM/YY',
                        'year': 'YY'
                    }
                }
            }]
        },
        plugins: {
            filler: {
                propagate: false
            }
        }
    };

    // Clean up data
    var cleanedContributor = {};
    var contributionsAmount = {};

    $.each(contributors, function (index, contributor) {
        var contributorId = contributor.name.replace(/\s+/g, '_');
        if(contributorId in cleanedContributor) {
            cleanedContributor[contributorId]['ways'] += contributor['ways'];
            cleanedContributor[contributorId]['nodes'] += contributor['nodes'];
            var timeline = JSON.parse(contributor.timeline);
            cleanedContributor[contributorId]['timeline'].concat(cleanedContributor[contributorId]['timeline'], timeline);
        } else {
            cleanedContributor[contributorId] = contributor;
            cleanedContributor[contributorId]['timeline'] =  JSON.parse(contributor.timeline)
        }
    });

    var allFrequencyDatasets = [];
    var allLabels = [];
    var color = Chart.helpers.color;

    $.each(cleanedContributor, function (key, contributor) {

        var frequencyDatasets = {
                label: contributor.name,
                borderColor : '#' + intToRGB(hashCode(contributor.name)),
                backgroundColor : color('#' + intToRGB(hashCode(contributor.name))).alpha(0.1).rgbString(),
                data: []
            };

        for(var i=0; i<contributor.timeline.length; i++) {
            var pair = contributor.timeline[i];
            var dateString = pair[0];
            var date = moment.utc(dateString, "YYYY-MM-DD");
            pair[0] = date.valueOf();
            contributor.timeline[i] = pair;

            if($.inArray(date, allLabels) === -1) {
                allLabels.push(date);
                frequencyDatasets.data.push({
                    x:date,
                    y:pair[1]
                })
            }

            var timeStamp = (date.unix()).toString();
            var isContributionDateExist = contributionsAmount[timeStamp]  !== undefined;
            if(isContributionDateExist) {
                contributionsAmount[timeStamp] += pair[1];
            } else {
                contributionsAmount[timeStamp] = pair[1];
            }
        }

        if($.inArray(start_date,allLabels) === -1){
            allLabels.push(start_date);
        }

        if($.inArray(end_date,allLabels) === -1){
            allLabels.push(end_date);
        }

        allFrequencyDatasets.push(frequencyDatasets);
    });

    allLabels = sortDate(allLabels);

    var frequencyDatasets = new Chart($('#user-frequency'), {
        type: 'line',
        options: frequencyOption,
        data: {
            labels: allLabels,
            datasets: allFrequencyDatasets
        }
    });

    contributionsAmount = sortObject(contributionsAmount);
    var contributionCtx = $('#contribution-amount');
    var contributionDatasets = {
            labels: allLabels,
            datasets: [{
                label: 'Contributors',
                borderColor : '#82afb8',
                backgroundColor : color('#82afb8').alpha(0.1).rgbString(),
                data: []
            }]
        };

    $.each(contributionsAmount, function (key, value) {
        var date = moment.unix(key);
        contributionDatasets.datasets[0].data.push({
                    x:date,
                    y:value
                });
    });

    new Chart(contributionCtx, {
        type: 'line',
        data: contributionDatasets,
        options: chartDateOption
    });

}

function sortDate(dateArray) {
    if(dateArray.length <= 1) {
        return dateArray;
    }

    var pivot = dateArray[0];

    var left = [];
    var right = [];

    for (var i=1; i < dateArray.length; i++) {
        dateArray[i] < pivot ? left.push(dateArray[i]) : right.push(dateArray[i]);
    }

    return sortDate(left).concat(pivot, sortDate(right))
}

function sortObject(o) {
    return Object.keys(o).sort().reduce((r, k) => (r[k] = o[k], r), {});
}

function createErrorPanel() {
     errorPanel = $('#feature-completeness-error-table').DataTable( {
         data: [],
         bFilter: false,
         bLengthChange: false,
         columns: [
            { title: "Name", "width": "20%"  },
            { title: "Date", "width": "20%" },
            { title: "Comment", "width": "50%" }
         ],
         columnDefs: [{
             targets: 1,
             render: function (data) {
                 var momentObj = moment(data, 'YYYY-MM-DDTHH:mm:ssZ');
                 return momentObj.format('YYYY-MM-DD');
             }
         }],
         responsive: true,
         order: [[ 1, "desc" ]]
    } );
}

function addRowToErrorPanel(row) {
    if(errorPanel) {
        errorPanel.row.add(row).draw(false);
    }
}

function renderInsightFunctions(username) {

    renderRemoteProjects();

    $.each(selected_functions, function (key, selected_function) {

        if (selected_function['name']) {
            var allow_function = true;
            if (selected_function['manager_only']) {
                if ($.inArray(username, managers) === -1) {
                    allow_function = false;
                }
            }
            if (allow_function) {
                var insightPanel = $('.advance-insights').clone()[0];
                var $insightPanel = $(insightPanel);
                $('.advance-insights-wrapper').append($insightPanel);
                $insightPanel.show();

                var $insightTitle = $insightPanel.find('.panel-heading');
                var $insightContent = $insightPanel.find('.panel-body');
                var tab_id = key;
                var tab_name = selected_function['name'];
                if(selected_function['feature']) {
                    tab_name += ' for ' + selected_function['feature'];
                }
                $insightTitle.html(tab_name);
                $insightContent.html(
                    '<div id="' + tab_id + '">' +
                        '<span class="grey-italic" style="margin-top:15px !important; position: absolute;"> Loading data .. </span>' +
                    '</div>'
                );
                getInsightFunctions(key);
                if (!containsObject(selected_function['feature'], feature_type_collected)) {
                    feature_type_collected.push(selected_function['feature']);
                }
            }
        }
    });

}

function calculateCampaignProgress() {
    var $campaignStatus = $('.detail-campaign-status');
    var $campaignStatusLabel = $('.detail-campaign-status label');

    if (start_date === 'None' || end_date === 'None') {
        $('.detail-campaign-status label').html('-');
        return;
    }

    start_date = moment(start_date, 'YYYY-MM-DD', true);
    end_date = moment(end_date, 'YYYY-MM-DD', true);

    var campaign_range = end_date.diff(start_date, 'days') + 1; // Include start

    if (campaign_range < 0) {
        $campaignStatusLabel.html('-');
        return;
    }

    var remaining_days = end_date.diff(moment(), 'days') + 1;

    var progress = 0;
    if (remaining_days <= 0) {
        progress = 100;
        if($campaignStatusLabel.text() == 'Inactive') {
            $campaignStatus.removeClass('running');
            $campaignStatus.addClass('finished');
            $campaignStatusLabel.html('Finished');
        }
    } else {
        progress = 100 - (remaining_days / campaign_range * 100);
        if(progress < 0){
            progress = 0
        }
    }

    $('#campaign-progress').css({
        'width': progress + '%'
    })
}

var insightTypeIndex = 0;
var errorFeatures = {
    'node': [],
    'way': [],
    'relation': []
};

function getInsightFunctions(function_id, function_name, type_id) {
    var url = '/campaign/' + uuid + '/' + function_id;
    var isFirstFunction = true;
    $.ajax({
        url: url,
        success: function (data) {
            var active = '';
            if (isFirstFunction) {
                active = 'active';
                isFirstFunction = false;
            }

            var $divFunction = $('#' + function_id);
            $divFunction.html(data);
            var $subContent = $divFunction.parent().next();

            if($divFunction.find('.total-features').length > 0) {
                var value = parseInt($divFunction.find('.total-features').html());
                total_features_collected += value;
                $('#features-collected').html(total_features_collected);

                if(typeof type_id !== 'undefined') {
                    var $currentTypeFeatureCollected = $('#type-'+type_id.replace(/\s+/g, '_') + ' .features-collected');
                    var currentValue = parseInt($currentTypeFeatureCollected.html()) || 0;
                    var totalValue = currentValue + value;
                    $currentTypeFeatureCollected.html(totalValue);

                    $('#total-features-'+type_id.replace(/\s+/g, '_')).html(
                        '<div class="insight-title" style="margin-bottom: 20px;margin-top: 20px;"> ' +
                            'Features Checked ' +
                            '<div class="completeness"> ' +
                                '<div class="type-insight-text">' +
                                    totalValue +
                                '</div>'+
                            '</div>'+
                        '</div>'
                    );
                }
            }

            if($divFunction.find('.insight-summaries').length > 0) {
                if(typeof type_id !== 'undefined') {
                    $('#'+type_id+'-summaries').append($divFunction.find('.insight-summaries').html());
                }
            }

            if(typeof type_id !== 'undefined') {
                if(function_name === 'FeatureAttributeCompleteness') {
                    for(var i=0; i<featureCompleteness.length;i++){
                        var idCol = $(featureCompleteness[i][0]);
                        errorFeatures[idCol.data('type')].push(idCol.data('id').toString());
                        addRowToErrorPanel(featureCompleteness[i]);
                    }

                    for (var key in featureData) {
                        if(featureData.hasOwnProperty(key)) {
                            renderFeatures(key, featureData[key], insightTypeIndex === 0);
                            insightTypeIndex++;
                        }
                    }

                    var totalError = parseInt($('#total-feature-completeness-errors').html());
                    $('#total-feature-completeness-errors').html(totalError + featureCompleteness.length);
                    getOSMCHAErrors();
                } else if (function_name === 'MapperEngagement') {
                    updateMapperEngagementTotal();
                }
            }

            if($divFunction.find('.update-status-information').length > 0)
            {
                $('#'+type_id+ ' .type-title').append('<div class="pull-right update-status">'+$divFunction.find('.update-status-information').html()+'</div>');
            }
        }
    });
}

function getOSMCHAErrors() {
    var url = '/campaign/osmcha_errors_data/'+ uuid +'?page_size=100';
    $.ajax({
        url: url,
        success: function (data) {

            var totalOsmchaErrors = parseInt(data["total"]);
            var totalError = parseInt($('#total-feature-completeness-errors').html());
            $('#total-feature-completeness-errors').html(totalError + totalOsmchaErrors);
            $.each(data["data"], function (index, error) {
                var rowData = [];
                rowData.push(
                    '<a target="_blank" href="https://osmcha.mapbox.com/changesets/'+error['ChangeSetId']+'">changesets :'+error['ChangeSetId']+'</a>'
                );
                rowData.push(moment(error['Date'], 'YYYY-MM-DD HH:mm').format());
                if(error['Reasons']) {
                    rowData.push('<div class="error-completeness">'+error['Reasons']+'</div>');
                } else {
                    rowData.push('<div class="error-completeness">'+error['Comment']+'</div>');
                }

                if(error['Features'].length > 0) {
                    for(var i=0; i < error['Features'].length; i++) {
                        var feature = error['Features'][i]['url'].split('-');
                        errorFeatures[feature[0]].push(feature[1]);
                    }
                }

                addRowToErrorPanel(rowData);
            })
        }
    });
}


function dictToTable(dictObject) {
    var result = '';
    for (var key in dictObject) {
        if(dictObject.hasOwnProperty(key)) {
            result += '<div>' +
                '<b>'+key+'</b> : '+ dictObject[key]+'</div>';
        }
    }
    return result;
}

function colorCompleteness(error_value) {

    var color = completenessPallete['100'];
    if(error_value == 100){
        color = completenessPallete['0'];
    } else if(error_value > 75){
        color = completenessPallete['25'];
    } else if(error_value > 50){
        color = completenessPallete['50'];
    } else if(error_value > 25){
        color = completenessPallete['75'];
    } else if(error_value > 0){
        color = completenessPallete['99'];
    } else {
        color = completenessPallete['100'];
    }

    return color;
}

function renderFeatures(feature_type, feature_data, show_feature) {
    var unusedNodes = {};
    var unusedWays = {};
    var ways = [];
    var relations = [];

    if(featureGroups.hasOwnProperty(feature_type)) {
        return;
    }

    if(show_feature) {
        featureGroups[feature_type] = L.featureGroup().addTo(map);
    } else {
        featureGroups[feature_type] = L.featureGroup();
    }
    var nodesGroup = L.featureGroup().addTo(featureGroups[feature_type]);
    var waysGroup = L.featureGroup().addTo(featureGroups[feature_type]);
    var relationsGroup = L.featureGroup().addTo(featureGroups[feature_type]);

    for(var i=0; i<feature_data.length; i++) {
        var feature = feature_data[i];
        var featureTag = '';

        if(feature.hasOwnProperty('tags')) {
            featureTag = 'Unknown';
            var featureTags = feature['tags'];
            if(featureTags.hasOwnProperty('amenity')) {
                featureTag = capitalizeFirstLetter(featureTags['amenity']);
            }
        } else {
            unusedNodes[feature['id']] = feature;
        }

        var completenessPercentage = (100 - feature['completeness']).toFixed(1);

        if(featureTag) {
            if(feature['type'] === 'node') {
                L.circle([feature['lat'],feature['lon']], 5, {
                    color: colorCompleteness(feature['completeness']),
                    fillColor: colorCompleteness(feature['completeness']),
                    fillOpacity: 0.7,
                    zIndexOffset: 999
                }).bindPopup(
                    '<div class="feature-detail"><h4>Feature - '+featureTag+'</h4>'+
                    '<div><a href="http://www.openstreetmap.org/node/' + feature['id'] + '" target="_blank"><b>http://www.openstreetmap.org/node/' + feature['id'] + '</b></a></div>'+
                        ((feature['error_message'] !== '') ? ('<div style="color:red"><b>error </b>: '+ feature['error_message'] + '</div>') : '') +
                        ((feature['warning_message'] !== '') ? ('<div style="color:orange"><b>warning </b>: '+ feature['warning_message'] + '</div>') : '') +
                    '<div><b>type </b>: node</div>'+
                    dictToTable(feature['tags']) + '<div><b>completeness </b>: '+completenessPercentage+'%</div>' +'</div>'
                ).addTo(nodesGroup);
            } else if(feature['type'] === 'way') {
                ways.push(feature);
            } else if(feature['type'] === 'relation') {
                relations.push(feature);
            }
        }
    }

    // Process ways
    for(i=0; i<ways.length; i++) {
        var way = ways[i];
        var latlngs = [];

        for(var n=0; n < way['nodes'].length; n++) {
            var node = way['nodes'][n];
            if(unusedNodes.hasOwnProperty(node)) {
                latlngs.push([
                    unusedNodes[node]['lat'],
                    unusedNodes[node]['lon']
                ])
            }
        }

        var wayTag = capitalizeFirstLetter(way['tags']['amenity']);
        var completenessPercentage = (100 - way['completeness']).toFixed(1);

        if(typeof wayTag !== 'undefined') {
            L.polygon(latlngs, {
                color: colorCompleteness(way['completeness']),
                fillColor: colorCompleteness(way['completeness']),
                fillOpacity: 0.5
            }).bindPopup(
                '<div class="feature-detail"><h4>Feature - '+wayTag+'</h4>'+
                '<div><a href="http://www.openstreetmap.org/way/' + way['id'] + '" target="_blank"><b>http://www.openstreetmap.org/way/' + way['id'] + '</b></a></div>'+
                    ((way['error_message'] !== '') ? ('<div style="color:red"><b>error </b>: '+ way['error_message'] + '</div>') : '') +
                    ((way['warning_message'] !== '') ? ('<div style="color:orange"><b>warning </b>: '+ way['warning_message'] + '</div>') : '') +
                '<div><b>type </b>: way</div>'+
                dictToTable(way['tags']) + '<div><b>completeness </b>: '+completenessPercentage+'%</div>' + '</div>'
            ).addTo(waysGroup);
        } else {
            unusedWays[way['id']] = way;
        }
    }

    // Process relation
    for (var r = 0; r < relations.length; r++) {
        var relation = relations[r];

        $.each(relation['members'], function (index, member) {
            if (!unusedWays.hasOwnProperty(member['ref'])) {
                return true;
            }

            var way = unusedWays[member['ref']];
            var latlngs = [];

            $.each(way['nodes'], function (index, node) {
                if (!unusedNodes.hasOwnProperty(node)) {
                    return true;
                }

                latlngs.push([
                    unusedNodes[node]['lat'],
                    unusedNodes[node]['lon']
                ]);
            });

            var fillOpacity = 0.0;

            if(member['role'] === 'inner') {
                fillOpacity = 0.5;
            }

            var relationTag = capitalizeFirstLetter(relation['tags']['amenity']);
            var completenessPercentage = (100 - relation['completeness']).toFixed(1);

            if(typeof relationTag !== 'undefined') {
                L.polygon(latlngs, {
                    color: colorCompleteness(relation['completeness']),
                    fillColor: colorCompleteness(relation['completeness']),
                    fillOpacity: fillOpacity
                }).bindPopup(
                    '<div class="feature-detail"><h4>Feature - '+relationTag+'</h4>'+
                    '<div><a href="http://www.openstreetmap.org/relation/' + relation['id'] + '" target="_blank"><b>http://www.openstreetmap.org/relation/' + relation['id'] + '</b></a></div>'+
                        ((relation['error_message'] !== '') ? ('<div style="color:red"><b>error </b>: '+ relation['error_message'] + '</div>') : '') +
                        ((relation['warning_message'] !== '') ? ('<div style="color:orange"><b>warning </b>: '+ relation['warning_message'] + '</div>') : '') +
                    '<div><b>type </b>: relation</div>'+
                    dictToTable(relation['tags']) + '<div><b>completeness </b>: '+completenessPercentage+'%</div>' + '</div>'
                ).addTo(relationsGroup);
            }
        });
    }

    featureGroups[feature_type].addLayer(relationsGroup);
    featureGroups[feature_type].addLayer(waysGroup);
    featureGroups[feature_type].addLayer(nodesGroup);

}

function renderInsightFunctionsTypes(username) {

    var campaignTypes = {};
    var $insightTabs = $('.insight-tabs');
    var $insightContent = $('.insight-content');
    var $insightFunctionPanel = $('.insight-function-panel');
    var index = 0;

    createErrorPanel();

    if (Object.keys(selected_functions).length === 0 && remote_projects.length === 0) {
        $insightFunctionPanel.html(
            '<h4 class="grey-italic">No insight Function</h4>'
        )
    } else {
        $insightTabs.show();
    }

    for (var key in campaign_types) {
        if (!campaign_types.hasOwnProperty(key)) {
            continue;
        }
        campaignTypes[campaign_types[key]['type']] = {};

        for(var selectedKey in selected_functions) {
            if(!selected_functions.hasOwnProperty(selectedKey)) {
                continue;
            }

            if(selected_functions[selectedKey]['type'] === campaign_types[key]['type']) {
                campaignTypes[campaign_types[key]['type']][selectedKey] =
                    selected_functions[selectedKey];
                delete selected_functions[selectedKey];
            }
        }
    }

    /***
    campaignTypes will contains this data:
    {"Educational Facilities":[
        {"function-2":{
            "function":"FeatureAttributeCompleteness",
            "category":"quality-function",
            "feature":"amenity=college,kindergarten,school,university",
            "attributes":"all",
            "type":"Educational Facilities",
            "type_required":"true",
            "manager_only":false,
            "name":"Showing feature completeness for Educational Facilities"}}]
    }
    ***/

    for (var campaignType in campaignTypes) {

        var tabName = campaignType;
        var tabId = tabName.replace(/\s+/g, '_');

        var active = '';
        if (index === 0) {
            activeInsightPanel = tabId;
            active = 'active';
        }

        $('.map-side-panel').append(
            '<div class="map-side-list map-side-type '+active+'" id="type-'+tabId+'" onclick="showInsightFunction(this, \''+tabId+'\')">'+
                '<div class="row">'+
                    '<div class="col-lg-12">'+
                        '<div class="pull-left map-side-list-name">'+
                                tabName +
                        '</div>'+
                        '<span class="pull-right map-side-list-number">'+
                                '<span class="features-collected">...</span>'+
                                '</span>'+
                    '</div>'+
                '</div>'+
                '<div id="'+tabId+'-summaries" class="side-panel-summaries"></div>'+
            '</div>'
        );

        $insightContent.find('#' + key).remove();
        $insightContent.append(
            '<div class="tab-pane fade ' + active + ' in" id="' + tabId + '"></div>'
        );

        var $typeContents = $('#'+tabId);

        $typeContents.append('<div class="row insight-type-content"></div>');
        $typeContents.append('<div class="row insight-type-sub-content"></div>');

        var $mainRowTypeContents = $('#'+tabId+ ' .insight-type-content');
        $mainRowTypeContents.append('<div class="type-title"><i class="fa fa-building" aria-hidden="true"></i> '+tabName+'</div>');

        var insightIndex = 1;
        $.each(campaignTypes[campaignType], function (key, selected_function) {

            if (selected_function['name']) {
                var allow_function = true;
                if (selected_function['manager_only']) {
                    if ($.inArray(username, managers) === -1) {
                        allow_function = false;
                    }
                }
                if (allow_function) {
                    var insightId = key;
                    var sizeColumn = 'col-lg-4';

                    if(selected_function['function'] === 'MapperEngagement') {
                        $mainRowTypeContents.append('<div id="'+insightId+'" style="display: none;"></div>')
                    } else {
                        $mainRowTypeContents.append(
                                '<div class="'+sizeColumn+' type-'+insightIndex+'" id="' + insightId + '">' +
                                '<span class="grey-italic" style="margin-top:15px !important; position: absolute;"> ' +
                                    'Loading data... </span>' +
                                '</div>'
                        );
                    }

                    if(insightIndex === Object.keys(campaignTypes[campaignType]).length) {
                        $mainRowTypeContents.append(
                                '<div class="'+sizeColumn+' type-'+insightIndex+'"" id="total-features-'+campaignType.replace(/\s+/g, '_')+'">' +
                                '<span class="grey-italic" style="margin-top:15px !important; position: absolute;"> ' +
                                    'Loading data... </span>' +
                                '</div>'
                        );
                    }

                    getInsightFunctions(insightId, selected_function['function'], tabId);
                    if (!containsObject(selected_function['feature'], feature_type_collected)) {
                        feature_type_collected.push(selected_function['feature']);
                    }

                    insightIndex++;
                }
            }
        });

        index++;
    }

    renderInsightFunctions(username);
}

function showInsightFunction(element, tabId) {
    var $divParent = $(element);
    map.fitBounds(drawnItems.getBounds());

    if($divParent.hasClass('active')) {
    } else {
        $('#'+activeInsightPanel).hide();
        map.removeLayer(featureGroups[activeInsightPanel]);
        $('#type-'+activeInsightPanel).removeClass('active');
        $divParent.addClass('active');
        $('#'+tabId).show();
        activeInsightPanel = tabId;
        map.addLayer(featureGroups[activeInsightPanel]);
    }
}

(renderInsights = function () {
   renderInsightFunctionsTypes('');
});

$('#download-xml').click(function (event) {
    var download_url = '/generate_josm';
    $('#download-xml').prop('disabled', true);
    var data = {};
    data['error_features'] = JSON.stringify(errorFeatures);
    $.ajax({
        type: "POST",
        url: download_url,
        data: data,
        success: function (data) {
            var dataDict = JSON.parse(data);
            if('file_name' in dataDict) {
                document.getElementById('download_xml_frame').src = '/download_josm/'+uuid+'/'+dataDict['file_name'];
            }
            $('#download-xml').prop('disabled', false);
        },
        error: function () {
            $('#download-xml').prop('disabled', false);
        }
    })
});
