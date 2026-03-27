# Reddit Accounts — Quick Reference

## Composio Config
- **API Key:** `ak_8E4M5xorY8qgqNN7W5u-`
- **User ID:** `pg-test-af819d82-c40c-431b-a51c-aff077f13733`
- **Auth Config:** `ac_0LOTHeKiftNv` (OAuth2, ENABLED)
- **Toolkit Version:** `20260312_00`
- **Client Script:** `scripts/reddit_client.py`

---

## Accounts

### Admin — Ava
| Field | Value |
|-------|-------|
| Reddit Username | u/Cool_Intention_161 |
| Display Name | Ava |
| Composio Account ID | `ca_ZopdlcjQQTkv` |
| User ID | `1wy7ui7llh` |
| Bio | Nobody warned me. Now I'm the Salesforce person. 5 yrs deep. Certified. |
| Karma | 1 |
| Created | Mar 2023 |
| Primary Subreddits | r/salesforce, r/salesforceadmin, r/SalesforceCertified, r/CRM |

### Developer — Marcus
| Field | Value |
|-------|-------|
| Reddit Username | u/Candid_Difficulty236 |
| Display Name | Marcus |
| Composio Account ID | `ca_1OLOcKSRPelp` |
| User ID | `29yvahy5ir` |
| Bio | Writing test classes since 2017. Still asking why. 7 yrs. Certified. |
| Karma | 1 |
| Created | Mar 2023 |
| Primary Subreddits | r/SalesforceDeveloper, r/salesforce, r/learnprogramming |

### Architect — depends_on_context
| Field | Value |
|-------|-------|
| Reddit Username | u/Sharp_Animal_2708 |
| Display Name | depends_on_context |
| Composio Account ID | `ca_bCe1XdcjrCiB` |
| User ID | `29yvymojkl` |
| Bio | Every answer depends on context. 12+ YOE. Architect certified. |
| Karma | 1 |
| Created | Mar 2023 |
| Primary Subreddits | r/Salesforce_Architects, r/salesforce, r/SalesforceDeveloper, r/sysadmin, r/consulting |

### Critic — trust_the_demo
| Field | Value |
|-------|-------|
| Reddit Username | u/SandboxIsProduction |
| Display Name | trust_the_demo |
| Composio Account ID | `ca_9tqOAgaeGw6m` |
| User ID | `29wjqt0nbk` |
| Bio | 10 yrs watching features go from keynote to shelfware. Not bitter. |
| Karma | 1 |
| Created | Mar 2023 |
| Primary Subreddits | r/CRM, r/salesforce, r/sysadmin, r/SaaS, r/consulting, r/technology |

---

## Available Reddit Tools (23)

### Content Creation
| Tool | Description |
|------|-------------|
| `REDDIT_CREATE_REDDIT_POST` | Create text or link post on a subreddit |
| `REDDIT_POST_REDDIT_COMMENT` | Reply to a post or comment |
| `REDDIT_EDIT_REDDIT_COMMENT_OR_POST` | Edit own comment or self-post |
| `REDDIT_DELETE_REDDIT_COMMENT` | Delete own comment |
| `REDDIT_DELETE_REDDIT_POST` | Delete own post |

### Content Retrieval
| Tool | Description |
|------|-------------|
| `REDDIT_RETRIEVE_REDDIT_POST` | Get hot/new/top/rising posts from a subreddit |
| `REDDIT_GET_R_TOP` | Get top posts with time filter |
| `REDDIT_GET` | Get posts from front page by sort |
| `REDDIT_GET_NEW` | (DEPRECATED) Get newest posts — use RETRIEVE instead |
| `REDDIT_GET_CONTROVERSIAL_POSTS` | Get controversial posts with time filters |
| `REDDIT_GET_RANDOM` | Get random post from any subreddit |
| `REDDIT_RETRIEVE_POST_COMMENTS` | Get all comments on a post |
| `REDDIT_RETRIEVE_SPECIFIC_COMMENT` | Get details of a specific comment or post |

### Search
| Tool | Description |
|------|-------------|
| `REDDIT_SEARCH_ACROSS_SUBREDDITS` | Search Reddit content with operators |
| `REDDIT_GET_SUBREDDITS_SEARCH` | Search for subreddits by topic/keyword |

### Subreddit Metadata
| Tool | Description |
|------|-------------|
| `REDDIT_GET_SUBREDDIT_RULES` | Get posting rules for a subreddit |
| `REDDIT_LIST_SUBREDDIT_POST_FLAIRS` | List available post flairs |
| `REDDIT_GET_USER_FLAIR` | Get user flair assignments |

### User & Account
| Tool | Description |
|------|-------------|
| `REDDIT_GET_REDDIT_USER_ABOUT` | Get user profile/karma info |
| `REDDIT_GET_ME_PREFS` | Get authenticated user preferences |
| `REDDIT_GET_USERNAME_AVAILABLE` | Check username availability |
| `REDDIT_GET_SCOPES` | List available OAuth scopes |

### Settings
| Tool | Description |
|------|-------------|
| `REDDIT_TOGGLE_INBOX_REPLIES` | Enable/disable inbox replies for a submission |
