package outscale

import (
	"os"
	"strconv"

	"github.com/hashicorp/terraform/helper/schema"
	"github.com/hashicorp/terraform/terraform"
)

// Provider ...
func Provider() terraform.ResourceProvider {

	fcu := "fcu"
	icu := "icu"

	o := os.Getenv("OUTSCALE_OAPI")

	isoapi, err := strconv.ParseBool(o)
	if err != nil {
		isoapi = false
	}

	if isoapi {
		fcu = "oapi"
	}

	return &schema.Provider{
		Schema: map[string]*schema.Schema{
			"access_key_id": {
				Type:        schema.TypeString,
				Required:    true,
				DefaultFunc: schema.EnvDefaultFunc("OUTSCALE_ACCESSKEYID", nil),
				Description: "The Access Key ID for API operations.",
			},
			"secret_key_id": {
				Type:        schema.TypeString,
				Required:    true,
				DefaultFunc: schema.EnvDefaultFunc("OUTSCALE_SECRETKEYID", nil),
				Description: "The Secret Key ID for API operations.",
			},
			"region": {
				Type:        schema.TypeString,
				Required:    true,
				DefaultFunc: schema.EnvDefaultFunc("OUTSCALE_REGION", nil),
				Description: "The Region for API operations.",
			},
			"oapi": {
				Type:        schema.TypeBool,
				Optional:    true,
				DefaultFunc: schema.EnvDefaultFunc("OUTSCALE_OAPI", false),
				Description: "Enable oAPI Usage",
			},
		},

		ResourcesMap: map[string]*schema.Resource{
			"outscale_vm":                        GetResource(fcu, "outscale_vm")(),
			"outscale_keypair":                   GetResource(fcu, "outscale_keypair")(),
			"outscale_keypair_importation":       GetResource(fcu, "outscale_keypair_importation")(),
			"outscale_image":                     GetResource(fcu, "outscale_image")(),
			"outscale_lin_internet_gateway_link": GetResource(fcu, "outscale_lin_internet_gateway_link")(),
			"outscale_lin_internet_gateway":      GetResource(fcu, "outscale_lin_internet_gateway")(),
			"outscale_lin":                       GetResource(fcu, "outscale_lin")(),
			"outscale_firewall_rules_set":        GetResource(fcu, "outscale_firewall_rules_set")(),
			"outscale_outbound_rule":             GetResource(fcu, "outscale_outbound_rule")(),
			"outscale_inbound_rule":              GetResource(fcu, "outscale_inbound_rule")(),
			"outscale_tag":                       GetResource(fcu, "outscale_tag")(),
			"outscale_public_ip":                 GetResource(fcu, "outscale_public_ip")(),
			"outscale_public_ip_link":            GetResource(fcu, "outscale_public_ip_link")(),
			"outscale_volume":                    GetResource(fcu, "outscale_volume")(),
			"outscale_volumes_link":              GetResource(fcu, "outscale_volumes_link")(),
			"outscale_vm_attributes":             GetResource(fcu, "outscale_vm_attributes")(),
			"outscale_lin_attributes":            GetResource(fcu, "outscale_lin_attributes")(),
			"outscale_nat_service":               GetResource(fcu, "outscale_nat_service")(),
			"outscale_subnet":                    GetResource(fcu, "outscale_subnet")(),
			"outscale_api_key":                   GetResource(icu, "outscale_api_key")(),
			"outscale_dhcp_option":               GetResource(fcu, "outscale_dhcp_option")(),
			"outscale_client_endpoint":           GetResource(fcu, "outscale_client_endpoint")(),
			"outscale_route":                     GetResource(fcu, "outscale_route")(),
			"outscale_route_table":               GetResource(fcu, "outscale_route_table")(),
			"outscale_route_table_link":          GetResource(fcu, "outscale_route_table_link")(),
			"outscale_dhcp_option_link":          GetResource(fcu, "outscale_dhcp_option_link")(),
			"outscale_vpn_connection":            GetResource(fcu, "outscale_vpn_connection")(),
			"outscale_vpn_gateway":               GetResource(fcu, "outscale_vpn_gateway")(),
			"outscale_vpn_gateway_link":          GetResource(fcu, "outscale_vpn_gateway_link")(),
			"outscale_vpn_connection_route":      GetResource(fcu, "outscale_vpn_connection_route")(),
		},
		DataSourcesMap: map[string]*schema.Resource{
			"outscale_vm":                    GetDatasource(fcu, "outscale_vm")(),
			"outscale_vms":                   GetDatasource(fcu, "outscale_vms")(),
			"outscale_firewall_rules_set":    GetDatasource(fcu, "outscale_firewall_rules_set")(),
			"outscale_firewall_rules_sets":   GetDatasource(fcu, "outscale_firewall_rules_sets")(),
			"outscale_image":                 GetDatasource(fcu, "outscale_image")(),
			"outscale_images":                GetDatasource(fcu, "outscale_images")(),
			"outscale_tag":                   GetDatasource(fcu, "outscale_tag")(),
			"outscale_tags":                  GetDatasource(fcu, "outscale_tags")(),
			"outscale_public_ip":             GetDatasource(fcu, "outscale_public_ip")(),
			"outscale_public_ips":            GetDatasource(fcu, "outscale_public_ips")(),
			"outscale_volume":                GetDatasource(fcu, "outscale_volume")(),
			"outscale_volumes":               GetDatasource(fcu, "outscale_volumes")(),
			"outscale_nat_service":           GetDatasource(fcu, "outscale_nat_service")(),
			"outscale_nat_services":          GetDatasource(fcu, "outscale_nat_services")(),
			"outscale_keypair":               GetDatasource(fcu, "outscale_keypair")(),
			"outscale_keypairs":              GetDatasource(fcu, "outscale_keypairs")(),
			"outscale_vm_state":              GetDatasource(fcu, "outscale_vm_state")(),
			"outscale_vms_state":             GetDatasource(fcu, "outscale_vms_state")(),
			"outscale_lin_internet_gateway":  GetDatasource(fcu, "outscale_lin_internet_gateway")(),
			"outscale_lin_internet_gateways": GetDatasource(fcu, "outscale_lin_internet_gateways")(),
			"outscale_subnet":                GetDatasource(fcu, "outscale_subnet")(),
			"outscale_subnets":               GetDatasource(fcu, "outscale_subnets")(),
			"outscale_lin":                   GetDatasource(fcu, "outscale_lin")(),
			"outscale_lins":                  GetDatasource(fcu, "outscale_lins")(),
			"outscale_lin_attributes":        GetDatasource(fcu, "outscale_lin_attributes")(),
			"outscale_client_endpoint":       GetDatasource(fcu, "outscale_client_endpoint")(),
			"outscale_client_endpoints":      GetDatasource(fcu, "outscale_client_endpoints")(),
			"outscale_route_table":           GetDatasource(fcu, "outscale_route_table")(),
			"outscale_route_tables":          GetDatasource(fcu, "outscale_route_tables")(),
			"outscale_vpn_gateway":           GetDatasource(fcu, "outscale_vpn_gateway")(),
			"outscale_api_key":               GetDatasource(fcu, "outscale_api_key")(),
			"outscale_vpn_gateways":          GetDatasource(fcu, "outscale_vpn_gateways")(),
		},

		ConfigureFunc: providerConfigureClient,
	}
}

func providerConfigureClient(d *schema.ResourceData) (interface{}, error) {
	config := Config{
		AccessKeyID: d.Get("access_key_id").(string),
		SecretKeyID: d.Get("secret_key_id").(string),
		Region:      d.Get("region").(string),
		OApi:        d.Get("oapi").(bool),
	}
	return config.Client()
}
