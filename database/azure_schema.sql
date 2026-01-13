-- Azure SQL Database Schema for Para Athletics
-- Run this script in Azure SQL to create the required tables

-- =====================================================
-- RANKINGS TABLE
-- Stores annual IPC rankings data
-- =====================================================
CREATE TABLE Rankings (
    id INT IDENTITY(1,1) PRIMARY KEY,
    year INT NOT NULL,
    rank INT,
    athlete_name NVARCHAR(200),
    nationality NVARCHAR(10),
    event_name NVARCHAR(100),
    classification NVARCHAR(20),
    performance NVARCHAR(50),
    competition NVARCHAR(200),
    date DATE,
    scraped_at DATETIME DEFAULT GETDATE(),

    INDEX IX_Rankings_Year (year),
    INDEX IX_Rankings_Athlete (athlete_name),
    INDEX IX_Rankings_Event (event_name),
    INDEX IX_Rankings_Classification (classification)
);

-- =====================================================
-- RECORDS TABLE
-- Stores world, Paralympic, regional records
-- =====================================================
CREATE TABLE Records (
    id INT IDENTITY(1,1) PRIMARY KEY,
    record_type NVARCHAR(50) NOT NULL,  -- 'World Record', 'Paralympic Record', etc.
    event_name NVARCHAR(100),
    performance NVARCHAR(50),
    athlete_name NVARCHAR(200),
    nationality NVARCHAR(10),
    location NVARCHAR(100),
    date DATE,
    competition NVARCHAR(200),
    wind_speed NVARCHAR(20),
    current_record BIT DEFAULT 1,  -- Is this the current record?
    scraped_at DATETIME DEFAULT GETDATE(),

    INDEX IX_Records_Type (record_type),
    INDEX IX_Records_Event (event_name),
    INDEX IX_Records_Athlete (athlete_name)
);

-- =====================================================
-- RESULTS TABLE
-- Stores competition results
-- =====================================================
CREATE TABLE Results (
    id INT IDENTITY(1,1) PRIMARY KEY,
    competition_name NVARCHAR(200),
    event_name NVARCHAR(100),
    athlete_name NVARCHAR(200),
    nationality NVARCHAR(10),
    classification NVARCHAR(20),
    performance NVARCHAR(50),
    performance_numeric FLOAT,  -- For sorting
    position INT,
    round NVARCHAR(50),  -- 'Final', 'Semi-Final', 'Heat 1', etc.
    date DATE,
    is_major_championship BIT DEFAULT 0,
    scraped_at DATETIME DEFAULT GETDATE(),

    INDEX IX_Results_Competition (competition_name),
    INDEX IX_Results_Event (event_name),
    INDEX IX_Results_Athlete (athlete_name),
    INDEX IX_Results_Nationality (nationality)
);

-- =====================================================
-- ATHLETES TABLE
-- Master athlete data with classification tracking
-- =====================================================
CREATE TABLE Athletes (
    id INT IDENTITY(1,1) PRIMARY KEY,
    athlete_name NVARCHAR(200) NOT NULL,
    nationality NVARCHAR(10),
    current_classification NVARCHAR(20),
    gender CHAR(1),  -- 'M' or 'F'
    birth_year INT,
    is_active BIT DEFAULT 1,
    notes NVARCHAR(500),
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE(),

    INDEX IX_Athletes_Name (athlete_name),
    INDEX IX_Athletes_Nationality (nationality),
    INDEX IX_Athletes_Classification (current_classification)
);

-- =====================================================
-- CLASSIFICATION_HISTORY TABLE
-- Track athlete classification changes over time
-- =====================================================
CREATE TABLE ClassificationHistory (
    id INT IDENTITY(1,1) PRIMARY KEY,
    athlete_id INT FOREIGN KEY REFERENCES Athletes(id),
    athlete_name NVARCHAR(200),
    old_classification NVARCHAR(20),
    new_classification NVARCHAR(20),
    effective_date DATE,
    reason NVARCHAR(200),
    created_at DATETIME DEFAULT GETDATE(),

    INDEX IX_ClassHistory_Athlete (athlete_id),
    INDEX IX_ClassHistory_Date (effective_date)
);

-- =====================================================
-- COMPETITIONS TABLE
-- Master list of competitions
-- =====================================================
CREATE TABLE Competitions (
    id INT IDENTITY(1,1) PRIMARY KEY,
    competition_name NVARCHAR(200) NOT NULL,
    location NVARCHAR(100),
    country NVARCHAR(10),
    start_date DATE,
    end_date DATE,
    is_major_championship BIT DEFAULT 0,  -- Paralympics, World Champs, etc.
    championship_type NVARCHAR(50),  -- 'Paralympic Games', 'World Championships', etc.

    INDEX IX_Competitions_Name (competition_name),
    INDEX IX_Competitions_Date (start_date)
);

-- =====================================================
-- SCRAPE_LOG TABLE
-- Track scraping activity
-- =====================================================
CREATE TABLE ScrapeLog (
    id INT IDENTITY(1,1) PRIMARY KEY,
    scrape_type NVARCHAR(50),  -- 'rankings', 'records', 'results'
    status NVARCHAR(20),  -- 'success', 'failed', 'partial'
    records_scraped INT,
    records_inserted INT,
    error_message NVARCHAR(500),
    started_at DATETIME,
    completed_at DATETIME,
    duration_seconds INT
);

-- =====================================================
-- SAUDI_ATHLETES VIEW
-- Quick access to Saudi (KSA) athletes
-- =====================================================
CREATE VIEW vw_SaudiAthletes AS
SELECT
    r.athlete_name,
    r.nationality,
    r.event_name,
    r.classification,
    r.performance,
    r.competition,
    r.date,
    r.year
FROM Rankings r
WHERE r.nationality = 'KSA'
UNION
SELECT
    res.athlete_name,
    res.nationality,
    res.event_name,
    res.classification,
    res.performance,
    res.competition_name as competition,
    res.date,
    YEAR(res.date) as year
FROM Results res
WHERE res.nationality = 'KSA';

-- =====================================================
-- CHAMPIONSHIP_STANDARDS VIEW
-- Calculate medal standards from results
-- =====================================================
CREATE VIEW vw_ChampionshipStandards AS
SELECT
    event_name,
    classification,
    competition_name,
    MIN(CASE WHEN position = 1 THEN performance_numeric END) as gold_standard,
    MIN(CASE WHEN position = 3 THEN performance_numeric END) as bronze_standard,
    MIN(CASE WHEN position = 8 THEN performance_numeric END) as finals_standard,
    COUNT(DISTINCT athlete_name) as athletes_count
FROM Results
WHERE is_major_championship = 1
  AND round = 'Final'
GROUP BY event_name, classification, competition_name;

-- =====================================================
-- STORED PROCEDURE: Update Athlete Classification
-- =====================================================
CREATE PROCEDURE sp_UpdateAthleteClassification
    @athlete_name NVARCHAR(200),
    @new_classification NVARCHAR(20),
    @effective_date DATE,
    @reason NVARCHAR(200) = NULL
AS
BEGIN
    DECLARE @athlete_id INT;
    DECLARE @old_classification NVARCHAR(20);

    -- Get athlete ID and current classification
    SELECT @athlete_id = id, @old_classification = current_classification
    FROM Athletes
    WHERE athlete_name = @athlete_name;

    -- Insert history record
    INSERT INTO ClassificationHistory (athlete_id, athlete_name, old_classification,
                                        new_classification, effective_date, reason)
    VALUES (@athlete_id, @athlete_name, @old_classification,
            @new_classification, @effective_date, @reason);

    -- Update current classification
    UPDATE Athletes
    SET current_classification = @new_classification,
        updated_at = GETDATE()
    WHERE id = @athlete_id;

    SELECT 'Classification updated successfully' as result;
END;
GO

-- =====================================================
-- STORED PROCEDURE: Get Athlete Profile
-- =====================================================
CREATE PROCEDURE sp_GetAthleteProfile
    @athlete_name NVARCHAR(200)
AS
BEGIN
    -- Basic info
    SELECT * FROM Athletes WHERE athlete_name = @athlete_name;

    -- Classification history
    SELECT * FROM ClassificationHistory
    WHERE athlete_name = @athlete_name
    ORDER BY effective_date DESC;

    -- Recent results
    SELECT TOP 20 * FROM Results
    WHERE athlete_name = @athlete_name
    ORDER BY date DESC;

    -- Rankings history
    SELECT * FROM Rankings
    WHERE athlete_name = @athlete_name
    ORDER BY year DESC, rank ASC;
END;
GO
