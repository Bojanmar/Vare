import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, Float, Date
import matplotlib.pyplot as plt
import seaborn as sns
from streamlit_option_menu import option_menu


# SQLAlchemy setup
DATABASE_URL = "sqlite:///measurements.db"
Base = declarative_base()

class Measurement(Base):
    __tablename__ = "measurements"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    surname = Column(String, index=True)
    date = Column(Date, index=True)
    full_rom = Column(Float)
    left = Column(Float)
    right = Column(Float)
    result = Column(String)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

# Apply rules function
def apply_rules(full_rom, left, right):
    if full_rom and left and right:
        # Rule 1
        if left <= full_rom / 2 or right <= full_rom / 2:
            if left <= right:
                return "From Incomplete Left Lateralization: Limited Both (Left Potentially Very Limited)"
            else:
                return "From Incomplete Right Lateralized: Limited Both (Right Potentially Very Limited)"
        
        # Rule 3
        if (full_rom / 2 < left <= full_rom - 10) or (full_rom / 2 < right <= full_rom - 10):
            if left <= right:
                return "From In-Tact Left Lateralized: Limited Left"
            else:
                return "From In-Tact Right Lateralized: Limited Right"
        
        # Rule 2
        if left <= full_rom - 10 or right <= full_rom - 10:
            if left <= right:
                return "From Functionally Left Lateralized: No Limit"
            else:
                return "From Functionally Right Lateralized: No Limit"
    
    return "No Match"

st.markdown(
    """
    <style>
    .centered-title {
        text-align: center;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Sidebar for basic info
with st.sidebar:
    st.image("images/sample_image.png", use_column_width=True)
    st.write("___________")


    st.markdown('<h1 class="centered-title">GRAVITY STUDIO</h1>', unsafe_allow_html=True)

# Navigation tabs
selected = option_menu(
    menu_title=None,
    options=["Add Measurement", "Search Measurements", "Delete Entries"],
    icons=["plus-circle", "search", "trash"],
    menu_icon="cast",
    default_index=0,
    orientation="horizontal",
)

# Define tests and full_rom values
tests = ["Shoulder IR", "Shoulder ER", "Shoulder Abduction", "Shoulder Flexion", "Trunk Rotation", "Ober's (Hip Adduction)",
         "Hip Abduction", "Hip Flexion", "Straight Leg Raise", "Hip IR", "Hip ER", "Foot Presentation"]
full_rom = [90, 90, 45, 140, 70, 45, 45, 90, 90, 40, 45, None]  # Add appropriate Full ROM values for each test

# Add Measurement Page
if selected == "Add Measurement":
    st.title("Measurement Input")

    # Input forms
    col1, col2, col3 = st.columns(3)
    with col1:
        name = st.text_input("Name", key="name_input")
    with col2:
        surname = st.text_input("Surname", key="surname_input")
    with col3:
        date = st.date_input("Date", datetime.today(), key="date_input")
    st.write("_________________________________________________")
    # Data tables and graph
    col_input, col_result, col_graph = st.columns(3)

    # Data input table
    data = {
        "Test": tests,
        "Full ROM": full_rom,
        "Left": [0.0] * len(tests),
        "Right": [0.0] * len(tests)
    }
    df = pd.DataFrame(data)
    st.write("_________________________________________________")
    with col_input:
        st.header("Input Data Table")
        edited_df = st.data_editor(df, use_container_width=True, height=450)

    if st.button("Submit", key="submit_button"):
        session = SessionLocal()
        results = []
        for index, row in edited_df.iterrows():
            test = row['Test']
            full_rom_value = row['Full ROM']
            left = row['Left']
            right = row['Right']
            
            if full_rom_value is not None:
                result = apply_rules(full_rom_value, left, right)
                measurement = Measurement(
                    name=name, surname=surname, date=date, 
                    full_rom=full_rom_value, left=left, right=right, result=result
                )
                session.add(measurement)
                results.append({
                    "Test": test,
                    "Full ROM": full_rom_value,
                    "Left": left,
                    "Right": right,
                    "Result": result
                })
        session.commit()
        session.close()
        st.success("Data submitted successfully!")

        with col_result:
            st.header("Results")
            result_df = pd.DataFrame(results)
            st.dataframe(result_df, height=450,width=600)
        
        with col_graph:
            st.header("Graph")
            # Plotting results
            result_df['Plot Value'] = result_df.apply(lambda row: row['Left'] if row['Left'] <= row['Right'] else row['Right'], axis=1)
            plt.figure(figsize=(10, 6.5))
            sns.set_palette("dark:#5A9_r")
            ax = sns.barplot(x='Test', y='Plot Value', data=result_df)
            ax.set_facecolor('none')  # Set axes face color to transparent
            plt.gca().set_facecolor('none')  # Set current axes face color to transparent
            plt.grid(False)  # Turn off the grid

            # Set font and line colors to white
            ax.tick_params(colors='white', which='both')  # Set tick colors
            ax.xaxis.label.set_color('white')  # Set x-axis label color
            ax.yaxis.label.set_color('white')  # Set y-axis label color
            ax.title.set_color('white')  # Set title color
            
            # Set spine color to white
            for spine in ax.spines.values():
                spine.set_edgecolor('white')

            plt.xlabel('Test')
            plt.ylabel('Values')
            plt.title('Test Results')
            plt.xticks(rotation=45, color='white')  # Set x-tick labels color
            plt.yticks(color='white')  # Set y-tick labels color
            # Set edge color of the plot
            fig = plt.gcf()
            fig.patch.set_edgecolor('white')  # Set edge color
            fig.patch.set_linewidth(2)  # Set edge line width

            
            st.pyplot(plt, transparent=True)
        
# Search Measurements Page
if selected == "Search Measurements":
    st.title("Search Measurements")

    st.header("Search Criteria")
    search_name = st.text_input("Search Name", key="search_name")
    search_surname = st.text_input("Search Surname", key="search_surname")
    search_date = st.date_input("Search Date", None, key="search_date")

    if st.button("Search", key="search_button"):
        session = SessionLocal()
        query = session.query(Measurement)
        if search_name:
            query = query.filter(Measurement.name.like(f'%{search_name}%'))
        if search_surname:
            query = query.filter(Measurement.surname.like(f'%{search_surname}%'))
        if search_date:
            query = query.filter(Measurement.date == search_date)
        
        results = query.all()
        session.close()
        
        if results:
            summary_data = [{
                'Name': r.name,
                'Surname': r.surname,
                'Date': r.date
            } for r in results]
            summary_df = pd.DataFrame(summary_data)

            selected_row = st.selectbox("Select Measurement", summary_df.apply(lambda row: f"{row['Date']} - {row['Name']} {row['Surname']}", axis=1))

            if selected_row:
                selected_measurement = results[summary_df.apply(lambda row: f"{row['Date']} - {row['Name']} {row['Surname']}", axis=1).tolist().index(selected_row)]
                detailed_data = [{
                    'Test': test,
                    'Full ROM': selected_measurement.full_rom,
                    'Left': selected_measurement.left,
                    'Right': selected_measurement.right,
                    'Result': selected_measurement.result
                } for test in tests]

                detailed_df = pd.DataFrame(detailed_data)
                col1,col2=st.columns(2)
                with col1:
                    st.dataframe(detailed_df,height=450)
                with col2:
                    # Plotting results for the selected test
                    detailed_df['Plot Value'] = detailed_df.apply(lambda row: row['Left'] if row['Left'] <= row['Right'] else row['Right'], axis=1)
                    plt.figure(figsize=(6, 3))
                    sns.set_palette("dark:#5A9_r")
                    ax = sns.barplot(x='Test', y='Plot Value', data=detailed_df)
                    ax.set_facecolor('none')  # Set axes face color to transparent
                    plt.gca().set_facecolor('none')  # Set current axes face color to transparent
                    plt.grid(False)  # Turn off the grid

                    # Set font and line colors to white
                    ax.tick_params(colors='white', which='both')  # Set tick colors
                    ax.xaxis.label.set_color('white')  # Set x-axis label color
                    ax.yaxis.label.set_color('white')  # Set y-axis label color
                    ax.title.set_color('white')  # Set title color
                    
                    # Set spine color to white
                    for spine in ax.spines.values():
                        spine.set_edgecolor('white')

                    plt.xlabel('Test', fontsize=6)
                    plt.ylabel('Values', fontsize=6)
                    plt.title('Test Results', fontsize=6)
                    plt.xticks(rotation=45, color='white', fontsize=6)  # Set x-tick labels color and font size
                    plt.yticks(color='white', fontsize=5)  # Set y-tick labels color and font size
                    # Set edge color of the plot
                    fig = plt.gcf()
                    fig.patch.set_edgecolor('white')  # Set edge color
                    fig.patch.set_linewidth(2)  # Set edge line width
                    st.pyplot(plt, transparent=True)
        else:
            st.write("No results found.")

    # Download functionality
    if st.button("Download All Measurements", key="download_button"):
        session = SessionLocal()
        measurements = session.query(Measurement).all()
        session.close()

        data = [{
            'Name': m.name,
            'Surname': m.surname,
            'Date': m.date,
            'Full ROM': m.full_rom,
            'Left': m.left,
            'Right': m.right,
            'Result': m.result
        } for m in measurements]
        
        df = pd.DataFrame(data)
        st.write(df)

        excel_path = 'measurements.xlsx'
        df.to_excel(excel_path, index=False)
        
        with open(excel_path, 'rb') as f:
            st.download_button('Download Excel', f, file_name='measurements.xlsx')

# Delete Entries Page
if selected == "Delete Entries":
    st.title("Delete Entries")

    st.header("All Measurements")
    session = SessionLocal()
    measurements = session.query(Measurement).all()
    session.close()

    if measurements:
        data = [{
            'ID': m.id,
            'Name': m.name,
            'Surname': m.surname,
            'Date': m.date,
            'Full ROM': m.full_rom,
            'Left': m.left,
            'Right': m.right,
            'Result': m.result
        } for m in measurements]
        
        df = pd.DataFrame(data)
        st.dataframe(df, height=450)

        st.subheader("Delete Specific Entry")
        entry_id = st.number_input("Enter the ID of the entry to delete", min_value=1, step=1)

        if st.button("Delete Entry"):
            session = SessionLocal()
            entry_to_delete = session.query(Measurement).filter(Measurement.id == entry_id).first()
            if entry_to_delete:
                session.delete(entry_to_delete)
                session.commit()
                st.success(f"Entry ID {entry_id} deleted successfully!")
            else:
                st.error("Entry not found")
            session.close()

        st.subheader("Delete All Entries")
        if st.button("Delete All Entries"):
            session = SessionLocal()
            session.query(Measurement).delete()
            session.commit()
            st.success("All entries deleted successfully!")
            session.close()
    else:
        st.write("No entries found.")

