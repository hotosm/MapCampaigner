function assignCampaignJsonToForm(json) {
    $('input#name').val(json['name']);
}

function checkCampaignJson() {
    clearNotification();
    var campaignJson = $('#advanced-mode-textarea').val();
    try {
        campaignJson = JSON.parse(campaignJson);
        assignCampaignJsonToForm(campaignJson);

        $("fieldset").each(function (index) {
            checkSteps(index);
        });
        checkFormHeader();
        //preparingStep(4);
    } catch (err) {
        showNotifications('Json format is not correct.', 'danger');
    }
}