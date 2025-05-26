import { saveGithubToken } from "../../api";
import { supabase } from "../../supabaseClient";
import { useNavigate } from "react-router-dom";

export default function GithubCallback() {
    const navigate = useNavigate();
    supabase.auth.onAuthStateChange(async (_, session) => {
        if (session) {
            console.log('Supabase session:', session);

            if (session.provider_token && session.user.app_metadata.provider === 'github') {
                const githubAccessToken = session.provider_token;

                console.log('GitHub Access Token:', githubAccessToken);

                await saveGithubToken(githubAccessToken);
            }

            navigate('/github-connect');
        }
    });
    return (<></>)
}