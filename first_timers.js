import { BskyAgent } from "@atproto/api";

export const agent = new BskyAgent({
  // App View URL
  service: "https://public.api.bsky.app",
  // If you were making an authenticated client, you would
  // use the PDS URL here instead - the main one is bsky.social
  // service: "https://bsky.social",
});

import { streamFirehose } from "./stream.js"

export function batchFirehose(on_batch) {
    let posts = [];

    return streamFirehose((data) => {
        // Only process posts, ignore replies
        if (data.kind != "commit" || data.commit.record == null || data.commit.record.$type != "app.bsky.feed.post" || data.commit.record.reply != null) {
            return;
        }

        posts.push(data);
        if (posts.length == 25) {
            on_batch(posts);
            posts = [];
        }
    });
}

export async function getFirstTimers(posts) {
    let results = [];
    const dids = posts.map((post) => post.did);
    let dids_to_posts = posts.reduce((acc, post) => {
        acc[post.did] = (acc[post.did] || []).concat([post]);
        return acc;
    }, {});

    try {
        const profiles = await agent.app.bsky.actor.getProfiles({
            actors: dids
        });

        for (const profile of profiles.data.profiles) {
            if (profile.postsCount == 1) {
                if (dids_to_posts[profile.did].length != 1) {
                    throw new Error(`Found more than one post for ${profile.did} (${profile.handle})!`);
                }

                results.push({
                    did: profile.did,
                    post: dids_to_posts[profile.did][0],
                    profile: profile
                });
            }
        }
    } catch (e) {
        console.error(`Error fetching profiles for chunk:`, e);
    }

    return results;
}   