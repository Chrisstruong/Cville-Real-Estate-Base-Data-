\copy real_estate_current_assessment (
    parcel_number,
    current_assessed_value,
    object_id,
    st_number,
    st_name,
    st_unit,
    legal_description,
    lot_sqft
)
FROM 'C:\Users\truongm\MinhTrietTruong\projects\real-estate-ai\data\Real_Estate_(Current_Assessments).csv'
WITH (
    FORMAT csv,
    HEADER true
);