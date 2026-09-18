import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from models import SuperSummary, Card, SlackInstallation

logger = logging.getLogger(__name__)

def build_briefing_blocks(super_summary: SuperSummary, cards: list[Card], app_url: str) -> list[dict]:
    """
    Constructs a Slack Block Kit payload for a daily briefing.
    """
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"NewsBrief Daily: {super_summary.headline}",
                "emoji": True
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{super_summary.batch_date.strftime('%B %d, %Y')}*\n\n{super_summary.synthesis}"
            }
        },
        {
            "type": "divider"
        }
    ]
    
    # Add an audio link button if available
    if super_summary.audio_url:
        full_audio_url = f"{app_url}{super_summary.audio_url}"
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "🎧 Listen to Audio Briefing"
                    },
                    "url": full_audio_url,
                    "action_id": "listen_audio"
                }
            ]
        })
        blocks.append({"type": "divider"})
        
    for card in cards:
        bullets_text = "\n".join([f"• {b}" for b in card.bullets])
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{card.headline}*\n{bullets_text}\n\n_Source: <{card.source_url}|{card.source_name}>_"
            },
            "accessory": {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "Read Deep Dive",
                    "emoji": True
                },
                "value": str(card.cluster_id),
                "url": f"{app_url}/deep-dive/{card.cluster_id}",
                "action_id": f"deep_dive_{card.id}"
            }
        })
        blocks.append({"type": "divider"})
        
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": "You received this because your team is subscribed to NewsBrief."
            }
        ]
    })
    
    return blocks

def send_slack_briefing(installation: SlackInstallation, blocks: list[dict]) -> bool:
    """
    Sends the constructed Block Kit payload to the designated Slack channel.
    """
    client = WebClient(token=installation.bot_token)
    try:
        response = client.chat_postMessage(
            channel=installation.channel_id,
            blocks=blocks,
            text="Your NewsBrief Daily is here!" # Fallback text
        )
        logger.info(f"Successfully posted Slack message to {installation.channel_id}: {response['ts']}")
        return True
    except SlackApiError as e:
        logger.error(f"Error sending Slack message: {e.response['error']}")
        return False
