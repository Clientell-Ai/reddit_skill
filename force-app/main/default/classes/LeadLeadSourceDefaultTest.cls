/**
 * @description Test class for LeadLeadSourceDefault trigger behavior.
 */
@IsTest
public with sharing class LeadLeadSourceDefaultTest {

    /**
     * @description Verifies LeadSource defaults to Web when blank.
     */
    @IsTest
    static void testLeadSourceDefault_Blank_BecomesWeb() {
        User u = [
            SELECT Id
            FROM User
            WHERE Id = :UserInfo.getUserId()
            WITH USER_MODE
            LIMIT 1
        ];
        System.runAs(u) {
            if (!Schema.sObjectType.Lead.isCreateable()) {
                System.assert(false, 'Lead should be creatable in test context');
            }

            Lead l = new Lead(
                LastName = 'BlankSource',
                Company = 'TestCo'
            );

            Test.startTest();
            insert l;
            Test.stopTest();

            System.assertEquals(
                'Web',
                l.LeadSource,
                'LeadSource should default to Web when blank'
            );
        }
    }

    /**
     * @description Verifies existing LeadSource is not overwritten.
     */
    @IsTest
    static void testLeadSourceExisting_Unchanged() {
        User u = [
            SELECT Id
            FROM User
            WHERE Id = :UserInfo.getUserId()
            WITH USER_MODE
            LIMIT 1
        ];
        System.runAs(u) {
            if (!Schema.sObjectType.Lead.isCreateable()) {
                System.assert(false, 'Lead should be creatable in test context');
            }

            Lead l = new Lead(
                LastName = 'HasSource',
                Company = 'TestCo',
                LeadSource = 'Phone Inquiry'
            );

            Test.startTest();
            insert l;
            Test.stopTest();

            System.assertEquals(
                'Phone Inquiry',
                l.LeadSource,
                'LeadSource should remain unchanged when provided'
            );
        }
    }

    /**
     * @description Verifies bulk insert mixed values.
     */
    @IsTest
    static void testLeadSourceBulk_MixedValues() {
        User u = [
            SELECT Id
            FROM User
            WHERE Id = :UserInfo.getUserId()
            WITH USER_MODE
            LIMIT 1
        ];
        System.runAs(u) {
            if (!Schema.sObjectType.Lead.isCreateable()) {
                System.assert(false, 'Lead should be creatable in test context');
            }

            List<Lead> leads = new List<Lead>{
                new Lead(LastName = 'Bulk1', Company = 'TestCo'),
                new Lead(LastName = 'Bulk2', Company = 'TestCo', LeadSource = 'Webinar'),
                new Lead(LastName = 'Bulk3', Company = 'TestCo', LeadSource = 'Referral'),
                new Lead(LastName = 'Bulk4', Company = 'TestCo')
            };

            Test.startTest();
            insert leads;
            Test.stopTest();

            System.assertEquals(
                'Web',
                leads[0].LeadSource,
                'Blank LeadSource should default to Web in bulk'
            );
            System.assertEquals(
                'Webinar',
                leads[1].LeadSource,
                'Existing LeadSource should remain unchanged in bulk'
            );
            System.assertEquals(
                'Referral',
                leads[2].LeadSource,
                'Existing LeadSource should remain unchanged in bulk'
            );
            System.assertEquals(
                'Web',
                leads[3].LeadSource,
                'Blank LeadSource should default to Web in bulk'
            );
        }
    }
}
