import streamlit as st
import numpy as np
import pandas as pd
import json

st.set_page_config(page_title="ARC-2026 Reasoning Playground", layout="wide")

st.title("🧩 ARC-2026 Reasoning Playground")
st.markdown("Automated Verification Suite, Interactive Reasoning Playground & Compositional Macros")

# Sidebar for Task Loader
st.sidebar.header("Task Loader")
task_option = st.sidebar.selectbox("Select Task Source", ["Sample Tasks", "Upload JSON"])

input_grid = None
expected_output = None

if task_option == "Sample Tasks":
    # Mock some sample tasks
    sample = st.sidebar.selectbox("Choose Sample", ["Task A: Rotate", "Task B: Gravity"])
    if sample == "Task A: Rotate":
        input_grid = np.array([[1, 2], [3, 4]])
        expected_output = np.array([[3, 1], [4, 2]])
    else:
        input_grid = np.array([[1, 0], [0, 2]])
        expected_output = np.array([[0, 0], [1, 2]])

elif task_option == "Upload JSON":
    uploaded_file = st.sidebar.file_uploader("Upload ARC Task JSON", type=["json"])
    if uploaded_file is not None:
        try:
            task_data = json.load(uploaded_file)
            # Assuming standard ARC JSON structure: train[0].input
            input_grid = np.array(task_data['train'][0]['input'])
            expected_output = np.array(task_data['train'][0]['output'])
        except Exception as e:
            st.sidebar.error(f"Error parsing JSON: {e}")

# Function to render colored grids
def render_grid(grid, title):
    st.subheader(title)
    # Simple color mapping for demonstration (ARC uses 0-9)
    colors = {
        0: '#000000', 1: '#0074D9', 2: '#FF4136', 3: '#2ECC40',
        4: '#FF851B', 5: '#AAAAAA', 6: '#F012BE', 7: '#FFDC00',
        8: '#7FDBFF', 9: '#85144b'
    }

    html = '<table style="border-collapse: collapse; margin-bottom: 20px;">'
    for row in grid:
        html += '<tr>'
        for val in row:
            color = colors.get(val, '#FFFFFF')
            html += f'<td style="width: 30px; height: 30px; background-color: {color}; border: 1px solid #555; text-align: center; color: white; font-weight: bold;">{val}</td>'
        html += '</tr>'
    html += '</table>'
    st.markdown(html, unsafe_allow_html=True)

if input_grid is not None and expected_output is not None:
    col1, col2 = st.columns(2)
    with col1:
        render_grid(input_grid, "Input Grid")
    with col2:
        render_grid(expected_output, "Expected Output")

    st.divider()

    # Beam Search Monitoring
    st.header("🔍 Beam Search Monitoring")
    if st.button("Run Solver"):
        with st.spinner("Searching for symbolic transformations..."):
            # Mock running the solver
            import time
            from solver.enumerator import BeamSearch

            search = BeamSearch(beam_width=3, max_depth=5)
            success, final_grid, trace = search.solve(input_grid, expected_output)

            st.metric("Active Search Depth", search.current_depth)
            st.metric("Candidates Evaluated", search.candidates_evaluated)
            st.metric("Cumulative Execution Time", f"{search.cumulative_time:.4f} sec")

            if success:
                st.success("✅ Symbolic Search Successful!")
                st.write(f"Trace: `{' -> '.join(trace)}`")
                render_grid(final_grid, "Solver Output")
            else:
                st.error("❌ Symbolic Search Failed. Triggering LLM Surgical Lifeline...")

                # Surgical CoT Display
                st.subheader("LLM Surgical Lifeline Activated")
                st.markdown("**Prompt:**")
                st.code(f"Input: {input_grid.tolist()}\nExpected: {expected_output.tolist()}\nWrite Python code to transform Input to Expected.", language="text")

                st.markdown("**Chain-of-Thought (CoT):**")
                st.info("The input is a 2x2 grid. I need to swap the elements across the diagonal to match the expected output. Let's apply a rotation or transpose operation.")

                st.markdown("**Corrective Code Generated:**")
                st.code('''import numpy as np\ndef transform(grid):\n    return np.rot90(grid, k=-1)''', language="python")

    st.divider()

    # Interactive Grid Sandbox
    st.header("🕹️ Interactive Grid Sandbox")
    st.write("Edit the input grid cells to test 'what-if' transformations.")

    # Simple editable dataframe for sandbox
    df = pd.DataFrame(input_grid)
    edited_df = st.data_editor(df)

    if st.button("Apply Rotate 90 to Sandbox"):
        from core.primitives import rotate_90
        try:
            sandbox_grid = edited_df.to_numpy()
            res = rotate_90(sandbox_grid)
            render_grid(res, "Sandbox Result (Rotate 90)")
        except Exception as e:
            st.error(e)

else:
    st.info("Please select or upload a task from the sidebar.")
