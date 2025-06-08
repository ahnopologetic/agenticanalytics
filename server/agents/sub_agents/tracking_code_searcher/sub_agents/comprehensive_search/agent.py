from google.adk.agents import LlmAgent
from agents.shared.tools import lc_shell_tool


comprehensive_search_agent = LlmAgent(
    name="comprehensive_search_agent",
    description="A agent that can search the codebase for tracking code",
    # model=LiteLlm(model="openai/gpt-4o-mini"),
    model="gemini-2.0-flash",
    instruction="""
Now, we will perform a deep search for the actual code patterns used by these libraries across all supported languages. We will save everything into a single raw data file.

Based on the output from the dependency reconnaissance agent, we will now search the codebase for the actual code patterns used by these libraries across all supported languages.

### Dependency Reconnaissance Output
{{ dependency_reconnaissance_output }}

Before we start, make sure we have rg installed.
```bash
which rg
```
If not, stop and ask the user to install it.

First, create a clean file for our results. Make sure to create the file in current directory.
Next, run the following `ripgrep` commands. They are designed to find the common function and method calls for each service across JavaScript, Swift, Kotlin, Ruby, and Go.
From the information provided by the dependency reconnaissance agent, we will now search the codebase for the actual code patterns used by these libraries across all supported languages.

```bash
# Create a clean file for our results. Make sure to create the file in current directory.
export CURRENT_DIR=$(pwd)
touch $CURRENT_DIR/potential_tracking_calls.txt
export POTENTIAL_TRACKING_CALLS_FILE=$CURRENT_DIR/potential_tracking_calls.txt
echo "Potential Tracking Calls File: $POTENTIAL_TRACKING_CALLS_FILE"
cd {{ dependency_reconnaissance_output.project_path }}
export PROJECT_PATH='$(pwd)'
echo 'Project path: $PROJECT_PATH'
export CONTEXT_FLAGS='-A 3 -B 3'
# if project path is not the same as current directory, move to project path
if [ "$PROJECT_PATH" != "$(pwd)" ]; then
    cd $PROJECT_PATH
fi

# decide which sdk is used in the project
echo 'SDK: {{ dependency_reconnaissance_output.tracking_sdk }}'
export SDK='{{ dependency_reconnaissance_output.tracking_sdk }}'

# Universal keywords (high signal), always run this first
rg --vimgrep $CONTEXT_FLAGS -e 'log_event\(' -e 'send_event\(' -e 'logEvent\(' -e 'trackEvent\('  >> $POTENTIAL_TRACKING_CALLS_FILE

# Based on the SDK, run one of the following commands
# Google Analytics (gtag.js, analytics.js, Firebase)
if [ "$SDK" == "google_analytics" ]; then
    echo "# Google Analytics (gtag.js, analytics.js, Firebase):" >> $POTENTIAL_TRACKING_CALLS_FILE
    rg --vimgrep $CONTEXT_FLAGS -e "gtag\('event'" -e "ga\('send', 'event'" -e "logEvent\(" -e "firebase\.analytics\(\)\.logEvent\("  >> $POTENTIAL_TRACKING_CALLS_FILE
elif [ "$SDK" == "firebase_analytics" ]; then
    echo "# Firebase Analytics:" >> $POTENTIAL_TRACKING_CALLS_FILE
    rg --vimgrep $CONTEXT_FLAGS -e "logEvent\(" -e "firebase\.analytics\(\)\.logEvent\("  >> $POTENTIAL_TRACKING_CALLS_FILE
elif [ "$SDK" == "firebase_analytics" ]; then
    echo "# Firebase Analytics:" >> $POTENTIAL_TRACKING_CALLS_FILE
    rg --vimgrep $CONTEXT_FLAGS -e "logEvent\(" -e "firebase\.analytics\(\)\.logEvent\("  >> $POTENTIAL_TRACKING_CALLS_FILE
elif [ "$SDK" == "gtag" ]; then
    echo "# GTag:" >> $POTENTIAL_TRACKING_CALLS_FILE
    rg --vimgrep $CONTEXT_FLAGS -e "gtag\('event'" -e "ga\('send', 'event'" -e "logEvent\("  >> $POTENTIAL_TRACKING_CALLS_FILE
elif [ "$SDK" == "segment" ]; then
    echo "# Segment:" >> $POTENTIAL_TRACKING_CALLS_FILE
    rg --vimgrep $CONTEXT_FLAGS -e "analytics\.track\('" -e "Analytics\.track\('" -e "enqueue\s*\(\s*analytics\.Track"  >> $POTENTIAL_TRACKING_CALLS_FILE
elif [ "$SDK" == "mixpanel" ]; then
    echo "# Mixpanel:" >> $POTENTIAL_TRACKING_CALLS_FILE
    rg --vimgrep $CONTEXT_FLAGS -e "mixpanel\.track\('" -e "Mixpanel\.mainInstance\(\)\.track\('" -e "Mixpanel\.logEvent\('" -e "mixpanel\.track_pageview\('"  >> $POTENTIAL_TRACKING_CALLS_FILE
elif [ "$SDK" == "amplitude" ]; then
    echo "# Amplitude:" >> $POTENTIAL_TRACKING_CALLS_FILE
    rg --vimgrep $CONTEXT_FLAGS -e "amplitude\.logEvent\('" -e "Amplitude\.instance\(\)\.logEvent\('" -e "amplitude\.Event\{"  >> $POTENTIAL_TRACKING_CALLS_FILE
elif [ "$SDK" == "rudderstack" ]; then
    echo "# Rudderstack:" >> $POTENTIAL_TRACKING_CALLS_FILE
    rg --vimgrep $CONTEXT_FLAGS -e "rudderanalytics\.track\('" -e "Rudder\.sharedInstance\(\)\.track\('" -e "RudderClient\.getInstance\(\)\.track\('"  >> $POTENTIAL_TRACKING_CALLS_FILE
elif [ "$SDK" == "mparticle" ]; then
    echo "# mParticle:" >> $POTENTIAL_TRACKING_CALLS_FILE
    rg --vimgrep $CONTEXT_FLAGS -e "mp\.logEvent\('" -e "MParticle\.sharedInstance\(\)\.logEvent\('" -e "MParticle\.logEvent\('"  >> $POTENTIAL_TRACKING_CALLS_FILE
elif [ "$SDK" == "posthog" ]; then
    echo "# PostHog:" >> $POTENTIAL_TRACKING_CALLS_FILE
    rg --vimgrep $CONTEXT_FLAGS -e "posthog\.capture\('" -e "PHGPostHog\.shared\(\)\?\.capture\('"  >> $POTENTIAL_TRACKING_CALLS_FILE
elif [ "$SDK" == "pendo" ]; then
    echo "# Pendo:" >> $POTENTIAL_TRACKING_CALLS_FILE
    rg --vimgrep $CONTEXT_FLAGS -e "pendo\.track\('" -e "PendoManager\.shared\(\)\.track\('"  >> $POTENTIAL_TRACKING_CALLS_FILE
elif [ "$SDK" == "heap" ]; then
    echo "# Heap:" >> $POTENTIAL_TRACKING_CALLS_FILE
    rg --vimgrep $CONTEXT_FLAGS -e "heap\.track\('" -e "Heap\.track\('"  >> $POTENTIAL_TRACKING_CALLS_FILE
elif [ "$SDK" == "snowplow" ]; then
    echo "# Snowplow:" >> $POTENTIAL_TRACKING_CALLS_FILE
    rg --vimgrep $CONTEXT_FLAGS -e "snowplow\('" -e "trackUnstructured\('" -e "SPSnowplow\.track\('" -e "Snowplow\.track\('"  >> $POTENTIAL_TRACKING_CALLS_FILE
fi

echo "Search complete. Raw results are in $POTENTIAL_TRACKING_CALLS_FILE"
```
This process creates a comprehensive text file containing all likely tracking calls, complete with file paths and surrounding code for context.
    """,
    tools=[lc_shell_tool],
    output_key="comprehensive_search_output",
    # after_agent_callback=validate_dependency_reconnaissance_output,
)
