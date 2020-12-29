# Title
st.title('Magic+ Dashboard')

# Header/Subheader
st.header('This is a header')

st.subheader('This is a subheader')

# Text
st.text('Text: Hello Streamlit')

# Markdown
st.markdown('### This is a Markdown')

# Error/Colorful Text
st.success('Successful')

st.info('Information!')

st.warning('This is a warning')

st.error('This is an error!')

st.exception('NameError("name three not defined")')

# Get Help Info About Python
st.help(range)

# Writing Text / Super Fxn
st.write('Text with write')
st.write(range(10))

# Images
from PIL import Image
img = Image.open('image1.png')
st.image(img, width=300, caption='Simple Image')

# # Video
# vid_file = open('example.mp4', 'rb').read()
# st.video(vid_file)

# Buttons
st.button('Simple Button')

if st.button('About'):
    st.text('This is Streamlit')

# Text Input
firstname = st.text_input('Enter a cust_nbr', 'Type here:')
if st.button('Submit'):
    result = firstname.title()
    st.success(result)

# Display interactive plotly chart
st.plotly_chart(plt)


def explore_data(dataset):
    df = pd.read_csv(os.path.join(dataset))
    return df