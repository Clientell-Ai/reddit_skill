/**
 * @description Tests for LeadLeadSourceDefault trigger defaulting LeadSource on insert.
 */
@IsTest
public with sharing class LeadLeadSourceDefaultTest {

    @IsTest
    static void defaultLeadSource_onInsert_variants() {
        User u = [SELECT Id FROM User WHERE Id = :UserInfo.getUserId() LIMIT 1];
        System.runAs(u) {
            System.assertEquals(true, Schema.sObjectType.Lead.isCreateable(), 'Lead should be creatable');
            System.assertEquals(true, Schema.sObjectType.Lead.isAccessible(), 'Lead should be accessible');

            List<Lead> leads = new List<Lead>{
                new Lead(LastName = 'NullSource', Company = 'Acme', LeadSource = null),
                new Lead(LastName = 'EmptySource', Company = 'Acme', LeadSource = ''),
                new Lead(LastName = 'ProvidedSource', Company = 'Acme', LeadSource = 'Phone Inquiry')
            };

            Test.startTest();
            Database.insert(leads, AccessLevel.USER_MODE);
            Test.stopTest();

            List<Lead> inserted = [
                SELECT Id, LeadSource
                FROM Lead
                WHERE Id IN :leads
                WITH USER_MODE
            ];

            Map<Id, Lead> byId = new Map<Id, Lead>(inserted);

            System.assertEquals('Web', byId.get(leads[0].Id).LeadSource, 'Null LeadSource should default to Web');
            System.assertEquals('Web', byId.get(leads[1].Id).LeadSource, 'Empty LeadSource should default to Web');
            System.assertEquals('Phone Inquiry', byId.get(leads[2].Id).LeadSource, 'Existing LeadSource should be preserved');
        }
    }
}
