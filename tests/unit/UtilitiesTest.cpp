#include "gtest/gtest.h"

#include "csv.hpp"

TEST(TestDataPipeline, TestParameter)
{
    EXPECT_EQ(1, 1);
}

TEST(TestDataPipeline, TestCSV)
{
    using namespace csv;

    //CSVReader reader("single_line_file.csv");
    auto csv_string = "integer, decimal, message\r\n"
                      "1, 2.3, Hello\r\n";

    csv::CSVReader rows = csv::parse(csv_string);

    auto first_row = *rows.begin(); // [index] is not yet supported
    EXPECT_EQ(first_row["integer"], 1);
    for (CSVRow &row : rows)
    { // Input iterator
        for (CSVField &field : row)
        {
            // By default, get<>() produces a std::string.
            // A more efficient get<string_view>() is also available, where the resulting
            // string_view is valid as long as the parent CSVRow is alive
            std::cout << field.get<>() << ", ";
        }
        std::cout << std::endl;
    }
}