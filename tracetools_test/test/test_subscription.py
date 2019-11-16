# Copyright 2019 Robert Bosch GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest

from tracetools_test.case import TraceTestCase


class TestSubscription(TraceTestCase):

    def __init__(self, *args) -> None:
        super().__init__(
            *args,
            session_name_prefix='session-test-subscription-creation',
            events_ros=[
                'ros2:rcl_node_init',
                'ros2:rcl_subscription_init',
                'ros2:rclcpp_subscription_init',
                'ros2:rclcpp_subscription_callback_added',
            ],
            nodes=['test_subscription'],
        )

    def test_all(self):
        # Check events as set
        self.assertEventsSet(self._events_ros)

        # Check fields
        rcl_sub_init_events = self.get_events_with_name('ros2:rcl_subscription_init')
        rclcpp_sub_init_events = self.get_events_with_name('ros2:rclcpp_subscription_init')
        callback_added_events = self.get_events_with_name(
            'ros2:rclcpp_subscription_callback_added',
        )

        for event in rcl_sub_init_events:
            self.assertValidHandle(
                event,
                ['subscription_handle', 'node_handle', 'rmw_subscription_handle'],
            )
            self.assertValidQueueDepth(event, 'queue_depth')
            self.assertStringFieldNotEmpty(event, 'topic_name')
        for event in rclcpp_sub_init_events:
            self.assertValidHandle(
                event,
                ['subscription_handle', 'subscription'],
            )
        for event in callback_added_events:
            self.assertValidHandle(event, ['subscription', 'callback'])

        # Check that the test topic name exists
        test_rcl_sub_init_events = self.get_events_with_field_value(
            'topic_name',
            '/the_topic',
            rcl_sub_init_events,
        )
        self.assertNumEventsEqual(test_rcl_sub_init_events, 1, 'cannot find test topic name')
        test_rcl_sub_init_event = test_rcl_sub_init_events[0]

        # Check queue_depth value
        self.assertFieldEquals(
            test_rcl_sub_init_event,
            'queue_depth',
            10,
            'sub_init event does not have expected queue depth value',
        )

        # Check that the node handle matches the node_init event
        node_init_events = self.get_events_with_name('ros2:rcl_node_init')
        test_sub_node_init_events = self.get_events_with_procname(
            'test_subscription',
            node_init_events,
        )
        self.assertNumEventsEqual(
            test_sub_node_init_events,
            1,
            'none or more than 1 node_init event',
        )
        test_sub_node_init_event = test_sub_node_init_events[0]
        self.assertMatchingField(
            test_sub_node_init_event,
            'node_handle',
            'ros2:rcl_subscription_init',
            rcl_sub_init_events,
        )

        # Check that subscription handle matches between rcl_sub_init and rclcpp_sub_init
        subscription_handle = self.get_field(test_rcl_sub_init_event, 'subscription_handle')
        rclcpp_sub_init_matching_events = self.get_events_with_field_value(
            'subscription_handle',
            subscription_handle,
            rclcpp_sub_init_events,
        )
        # Should only have 1 rclcpp_sub_init event, since intra-process is not enabled
        self.assertNumEventsEqual(
            rclcpp_sub_init_matching_events,
            1,
            'none or more than 1 rclcpp_sub_init event for topic',
        )

        # Check that subscription pointer matches between rclcpp_sub_init and sub_callback_added
        rclcpp_sub_init_matching_event = rclcpp_sub_init_matching_events[0]
        subscription_pointer = self.get_field(rclcpp_sub_init_matching_event, 'subscription')
        callback_added_matching_events = self.get_events_with_field_value(
            'subscription',
            subscription_pointer,
            callback_added_events,
        )
        self.assertNumEventsEqual(
            callback_added_matching_events,
            1,
            'none or more than 1 rclcpp_sub_callback_added event for topic',
        )


if __name__ == '__main__':
    unittest.main()
