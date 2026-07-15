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
    When I copy the "SKU" field
    And I press the "Clear" button
    Then the "SKU" field should be empty
    And the "Name" field should be empty
    And the "Description" field should be empty
    And the "Price" field should be empty
    And the "Image" field should be empty
    When I paste the "SKU" field
    And I press the "Retrieve" button
    Then I should see the message "Success"
    And I should see "Wireless Mouse" in the "Name" field
    And I should see "Ergonomic wireless mouse with silent click technology" in the "Description" field
    And I should see "29.99" in the "Price" field
    And I should see "https://example.com/images/wireless-mouse.jpg" in the "Image" field
    And I should see "ACTIVE" in the "State" dropdown