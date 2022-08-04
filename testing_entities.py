from inference_entities import SpacyTesting

def test():
    st = SpacyTesting()
    f1 = st.run()
    return f1