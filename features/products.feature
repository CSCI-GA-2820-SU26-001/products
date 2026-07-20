Feature: The product service back-end
    As a Store Owner
    I need a RESTful catalog service
    So that I can keep track of all my products

Background:
    Given the following products
    | sku | name                        | description                                           | price  | image                                                        | state        |
    | 1001| Wireless Mouse              | Ergonomic wireless mouse with silent click technology | 29.99  | https://example.com/images/wireless-mouse.jpg                | ACTIVE       |
    | 1002| Mechanical Keyboard         | RGB mechanical keyboard with blue switches            | 89.50  | https://example.com/images/mechanical-keyboard.jpg           | ACTIVE       |
    | 1003| USB-C Hub                   | 7-in-1 USB-C hub with HDMI and Ethernet ports         | 49.99  | https://example.com/images/usb-c-hub.jpg                     | INACTIVE     |
    | 1004| Noise Cancelling Headphones | Over-ear headphones with active noise cancellation    | 199.99 | https://example.com/images/noise-cancelling-headphones.jpg   | DISCONTINUED |

Scenario: The server is running
    When I visit the "Home Page"
    Then I should see "Product Demo RESTful Service" in the title
    And I should not see "404 Not Found"

Scenario: Create a Product
    When I visit the "Home Page"
    And I set the "SKU" to "3001"
    And I set the "Name" to "Wireless Mouse"
    And I set the "Description" to "Ergonomic wireless mouse with silent click technology"
    And I set the "Price" to "29.99"
    And I set the "Image" to "https://example.com/images/wireless-mouse.jpg"
    And I select "ACTIVE" in the "State" dropdown
    And I press the "Create" button
    Then I should see the message "Success"

Scenario: Deactivate a Product
    When I visit the "Home Page"
    And I set the "SKU" to "3001"
    And I set the "Name" to "Wireless Mouse"
    And I set the "Description" to "Ergonomic wireless mouse with silent click technology"
    And I set the "Price" to "29.99"
    And I set the "Image" to "https://example.com/images/wireless-mouse.jpg"
    And I select "ACTIVE" in the "State" dropdown
    And I press the "Create" button
    Then I should see the message "Success"
    And I should see "ACTIVE" in the "State" dropdown

    When I press the "Deactivate" button
    Then I should see the message "Success: product deactivated"
    And I should see "INACTIVE" in the "State" dropdown

Scenario: Activate a Product
    When I visit the "Home Page"
    And I set the "SKU" to "3001"
    And I set the "Name" to "Wireless Mouse"
    And I set the "Description" to "Ergonomic wireless mouse with silent click technology"
    And I set the "Price" to "29.99"
    And I set the "Image" to "https://example.com/images/wireless-mouse.jpg"
    And I select "INACTIVE" in the "State" dropdown
    And I press the "Create" button
    Then I should see the message "Success"
    And I should see "INACTIVE" in the "State" dropdown

    When I press the "Activate" button
    Then I should see the message "Success: product activated"
    And I should see "ACTIVE" in the "State" dropdown

Scenario: Discontinue a Product
    When I visit the "Home Page"
    And I set the "SKU" to "3001"
    And I set the "Name" to "Wireless Mouse"
    And I set the "Description" to "Ergonomic wireless mouse with silent click technology"
    And I set the "Price" to "29.99"
    And I set the "Image" to "https://example.com/images/wireless-mouse.jpg"
    And I select "INACTIVE" in the "State" dropdown
    And I press the "Create" button
    Then I should see the message "Success"
    And I should see "INACTIVE" in the "State" dropdown

    When I press the "Discontinue" button
    Then I should see the message "Success: product discontinued"
    And I should see "DISCONTINUED" in the "State" dropdown

Scenario: Deactivate an Inactive Product
    When I visit the "Home Page"
    And I set the "SKU" to "3001"
    And I set the "Name" to "Wireless Mouse"
    And I set the "Description" to "Ergonomic wireless mouse with silent click technology"
    And I set the "Price" to "29.99"
    And I set the "Image" to "https://example.com/images/wireless-mouse.jpg"
    And I select "INACTIVE" in the "State" dropdown
    And I press the "Create" button
    Then I should see the message "Success"
    And I should see "INACTIVE" in the "State" dropdown

    When I press the "Deactivate" button
    Then I should see the message "Success: product deactivated"
    And I should see "INACTIVE" in the "State" dropdown

Scenario: List Products
    When I visit the "Home Page"
    And I press the "Search" button
    Then I should see the message "Success"
    And I should see "Wireless Mouse" in the results
    And I should see "Mechanical Keyboard" in the results
    And I should see "USB-C Hub" in the results
    And I should see "Noise Cancelling Headphones" in the results
