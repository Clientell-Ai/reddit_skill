trigger LeadLeadSourceDefault on Lead (before insert) {
    for (Lead l : Trigger.new) {
        if (String.isBlank(l.LeadSource)) {
            l.LeadSource = 'Web';
        }
    }
}
